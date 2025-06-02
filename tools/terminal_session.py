
import os
import subprocess
import time
import uuid

class TerminalSession:
    def __init__(self, working_directory):
        self.session_name = f"superagent_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        self.working_directory = working_directory

        if subprocess.run("which tmux", shell=True, capture_output=True, text=True).returncode != 0:
            raise EnvironmentError("tmux is required for agent's shell functionality but not found. Please install tmux: sudo apt install tmux")

        subprocess.run(f"tmux kill-session -t {self.session_name}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.run(f"tmux new-session -d -s {self.session_name} -c '{self.working_directory}'", shell=True, check=True)
        print(f"[SuperAgent] Spawned visible tmux terminal session: {self.session_name}")
        print(f"[SuperAgent] To view or interact with the terminal, run: tmux attach-session -t {self.session_name}")

        # Get the pane id for the only pane in the new session
        pane_id_proc = subprocess.run(
            f"tmux list-panes -t {self.session_name} -F '#{{pane_id}}'", shell=True, capture_output=True, text=True
        )
        panes = pane_id_proc.stdout.strip().split("\n")
        if not panes or not panes[0]:
            raise RuntimeError(f"Could not retrieve tmux pane id for session {self.session_name}")
        self.pane_id = panes[0]
        print(f"[SuperAgent] Using tmux pane id: {self.pane_id}")

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
        max_wait = 60
        waited = 0
        poll_interval = 0.3
        output = ""
        found_end = False

        last_pane_dump = ""
        while waited < max_wait:
            pane_capture = subprocess.run(
                f"tmux capture-pane -t {self.pane_id} -p -S -500 -J",
                shell=True, capture_output=True, text=True
            )
            pane = pane_capture.stdout
            last_pane_dump = pane  # keep last for possible debugging

            if start_marker in pane and end_marker in pane:
                start_idx = pane.rfind(start_marker) + len(start_marker)
                end_idx = pane.rfind(end_marker)
                output = pane[start_idx:end_idx].strip()
                output = output.replace(f"echo {end_marker}", "")
                found_end = True
                break
            time.sleep(poll_interval)
            waited += poll_interval

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
        subprocess.run(f"tmux kill-session -t {self.session_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
