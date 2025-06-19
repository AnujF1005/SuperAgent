
import os
import subprocess
import time
import uuid
import sys
import platform

class TerminalSession:
    def __init__(self, working_directory):
        self.session_name = f"superagent_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        self.working_directory = os.path.abspath(working_directory)
        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory, exist_ok=True)
        self.terminal_process = None # To store the Popen object of the launched terminal

        if subprocess.run("which tmux", shell=True, capture_output=True, text=True).returncode != 0:
            raise EnvironmentError("tmux is required for agent's shell functionality but not found. Please install tmux: sudo apt install tmux")

        subprocess.run(f"tmux kill-session -t {self.session_name}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.run(f"tmux new-session -d -s {self.session_name} -c '{self.working_directory}'", shell=True, check=True)
        
        # Get the pane id for the only pane in the new session
        pane_id_proc = subprocess.run(
            f"tmux list-panes -t {self.session_name} -F '#{{pane_id}}'", shell=True, capture_output=True, text=True
        )
        panes = pane_id_proc.stdout.strip().split("\n")
        if not panes or not panes[0]:
            raise RuntimeError(f"Could not retrieve tmux pane id for session {self.session_name}")
        self.pane_id = panes[0]

        # Launch a visible terminal and attach to the tmux session
        attach_command = f"tmux attach-session -t {self.session_name}"
        
        if sys.platform.startswith('linux'):
            # Try common Linux terminals
            terminal_commands = [
                f"gnome-terminal -- bash -c '{attach_command}'",
                f"xterm -e '{attach_command}'",
                f"konsole --noclose -e '{attach_command}'"
            ]
            for cmd in terminal_commands:
                try:
                    self.terminal_process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
                    print(f"[SuperAgent] Launched visible terminal (Linux): {cmd}")
                    break
                except FileNotFoundError:
                    continue # Try next terminal
            if not self.terminal_process:
                print("[SuperAgent] WARNING: Could not find a suitable terminal emulator (gnome-terminal, xterm, konsole) on Linux.")
                print(f"[SuperAgent] To view or interact with the terminal, run: {attach_command}")

        elif sys.platform == 'darwin':
            # macOS Terminal.app
            script = f'''
            tell application "Terminal"
                do script "{attach_command}"
                activate
            end tell
            '''
            self.terminal_process = subprocess.Popen(['osascript', '-e', script], preexec_fn=os.setsid)
            print(f"[SuperAgent] Launched visible terminal (macOS): Terminal.app")

        elif sys.platform == 'win32':
            # Windows Command Prompt
            # Use `start` to open a new window and `/k` to keep it open after command
            cmd = f"start cmd.exe /k \"{attach_command}\""
            self.terminal_process = subprocess.Popen(cmd, shell=True)
            print(f"[SuperAgent] Launched visible terminal (Windows): cmd.exe")
        else:
            print(f"[SuperAgent] WARNING: Unsupported operating system '{sys.platform}'. Cannot launch visible terminal automatically.")
            print(f"[SuperAgent] To view or interact with the terminal, run: {attach_command}")

        time.sleep(1) # Give the terminal a moment to open

    def send_command_and_capture(self, command):
        start_marker = f"__SUPERAGENT_START_{uuid.uuid4().hex[:8]}__"
        end_marker = f"__SUPERAGENT_END_{uuid.uuid4().hex[:8]}__"

        # Send marker, command, and end marker, each followed by Enter
        subprocess.run(f"tmux send-keys -t {self.pane_id} 'echo {start_marker}' Enter", shell=True, check=True)
        subprocess.run(f"tmux send-keys -t {self.pane_id} '{command}' Enter", shell=True, check=True)
        subprocess.run(f"tmux send-keys -t {self.pane_id} 'echo {end_marker}' Enter", shell=True, check=True)

        # Allow moment for the command to run and flush
        time.sleep(0.4)

        # Poll and also log the full pane output for diagnosis
        max_wait = 600
        waited = 0
        poll_interval = 2
        output = ""
        found_end = False

        last_pane_dump = ""

        try:
            while waited < max_wait:
                pane_capture = subprocess.run(
                    f"tmux capture-pane -t {self.pane_id} -p -S -500 -J",
                    shell=True, capture_output=True, text=True
                )
                pane = pane_capture.stdout
                last_pane_dump = pane  # keep last for possible debugging

                pane = pane.replace(f"echo {end_marker}", "")

                if start_marker in pane and end_marker in pane:
                    start_idx = pane.rfind(start_marker) + len(start_marker)
                    end_idx = pane.rfind(end_marker)
                    output = pane[start_idx:end_idx].strip()
                    found_end = True
                    break
                time.sleep(poll_interval)
                waited += poll_interval
        except KeyboardInterrupt:
            print("[SuperAgent] Command capture interrupted by user.")
        except Exception as e:
            print(f"[SuperAgent] WARNING: Error capturing tmux pane output: {e}")
            output = f"[SuperAgent] ERROR: Failed to capture command output due to an error: {e}"

        # If still not found, dump log to disk for diagnosis:
        if not found_end:
            debug_path = f"/tmp/superagent_tmux_debug_{self.session_name}.txt"
            try:
                with open(debug_path, "w") as f:
                    f.write(f"START_MARKER: {start_marker}\nEND_MARKER: {end_marker}\n\nLAST_PANE_BUFFER:\n{last_pane_dump}\n")
            except Exception as e:
                pass
            output = f"[SuperAgent] ERROR: Timeout waiting for command output or marker.\nSee {debug_path} for diagnostic dump."

        return output

    def cleanup(self):
        # Terminate the launched terminal process if it exists
        if self.terminal_process and self.terminal_process.poll() is None:
            try:
                if sys.platform.startswith('linux') or sys.platform == 'darwin':
                    # On Unix-like systems, send SIGTERM to the process group
                    os.killpg(os.getpgid(self.terminal_process.pid), 15) # 15 is SIGTERM
                else:
                    self.terminal_process.terminate()
                self.terminal_process.wait(timeout=5) # Wait for process to terminate
            except Exception as e:
                print(f"[SuperAgent] WARNING: Error terminating terminal process: {e}")
                self.terminal_process.kill() # Force kill if graceful fails
        
        # Kill the tmux session
        subprocess.run(f"tmux kill-session -t {self.session_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
