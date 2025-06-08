
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os # Added import for environment variable access

class BrowserTool:
    name = "browser_actions"
    params = {
        "optional": ["query", "url"],
        "required": [],
    }
    description = """
    Request to launch a browser to perform one of two actions:
    1. Search a query on a search engine, navigate to the first result, and extract its text content.
    2. Directly open a specified URL and extract its text content.

    Provide EITHER 'query' OR 'url', but not both.
    Parameters:
    - query: (optional) The query to search on a search engine.
    - url: (optional) The exact URL to open directly.
    Usage for search:
    <browser_actions>
    <query>what is selenium</query>
    </browser_actions>

    Usage for opening a URL:
    <browser_actions>
    <url>https://www.example.com</url>
    </browser_actions>
    """
    examples = """
    Requesting to find information about Python:
    <browser_actions>
    <query>official python documentation</query>
    </browser_actions>

    Requesting to open a specific webpage:
    <browser_actions>
    <url>https://www.selenium.dev/documentation/</url>
    </browser_actions>
    """

    def __init__(self):
        self.driver = None

    def _initialize_driver(self):
        if self.driver is None:
            try:
                options = webdriver.ChromeOptions()
                # options.add_argument('--headless') # Run in headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu') # Optional, recommended for headless
                
                chrome_binary_path = os.environ.get('CHROME_BINARY_PATH')
                if chrome_binary_path:
                    options.binary_location = chrome_binary_path
                
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except WebDriverException as e:
                print(f"Error initializing WebDriver: {e}")
                print("Please ensure Chrome is installed and ChromeDriver is compatible or accessible.")
                self.driver = None # Ensure driver is None on failure
                raise
            except Exception as e:
                print(f"An unexpected error occurred during WebDriver initialization: {e}")
                self.driver = None # Ensure driver is None on failure
                raise

    def _extract_page_content(self, current_url: str):
        """Helper function to extract and limit page content."""
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2) # Allow dynamic content to load
        body_element = self.driver.find_element(By.TAG_NAME, "body")
        page_text = body_element.text
        return page_text

    def __call__(self, query: str = None, url: str = None):
        try:
            self._initialize_driver()
        except Exception as e:
            return f"Failed to initialize WebDriver: {e}"

        if url and query:
            return "Error: Provide either 'url' or 'query', not both."
        if not url and not query:
            return "Error: Provide either 'url' or 'query'."

        try:
            if url:
                # Action: Open URL directly
                self.driver.get(url)
                page_text = self._extract_page_content(current_url=url)
                return f"Successfully opened URL '{url}' and extracted content: {page_text}"

            elif query:
                # Action: Perform search
                self.driver.get("https://www.duckduckgo.com")
                search_bar = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_bar.clear()
                search_bar.send_keys(query)
                search_bar.send_keys(Keys.RETURN)

                first_result_selector = "(//a[contains(@class, 'result__a')])[1]" # More robust DuckDuckGo specific selector

                try:
                    first_result_link_element = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, first_result_selector))
                    )
                except TimeoutException:
                    return f"Could not find the first search result link for query: '{query}'."
                
                first_result_url = first_result_link_element.get_attribute("href")
                if not first_result_url:
                    return f"Found first result element, but it has no URL for query: '{query}'"

                self.driver.get(first_result_url)
                page_text = self._extract_page_content(current_url=first_result_url)
                return f"Successfully searched for '{query}', navigated to '{first_result_url}', and extracted content: {page_text}"

        except TimeoutException:
            action = "opening URL" if url else "performing search"
            target = url if url else query
            return f"Timeout while {action} '{target}'"
        except NoSuchElementException:
            action = "opening URL" if url else "performing search"
            target = url if url else query
            return f"Could not find a required element during {action} for '{target}'"
        except WebDriverException as e:
            action = "opening URL" if url else "performing search"
            target = url if url else query
            return f"WebDriver error during {action} for '{target}': {str(e)}"
        except Exception as e:
            action = "opening URL" if url else "performing search"
            target = url if url else query
            return f"An unexpected error occurred during browser operation for '{target}': {str(e)}"

    def quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error while quitting WebDriver: {e}")
            finally:
                self.driver = None

# Example of how the main agent might handle the driver lifecycle:
# if __name__ == '__main__':
#     tool = SearchTool()
#     if tool.driver: # Check if driver initialized successfully
#         print(tool(query="latest news on AI"))
#         tool.quit_driver()
#     else:
#         print("Browser tool could not be initialized.")
