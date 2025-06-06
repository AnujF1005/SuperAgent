
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

class SearchTool:
    name = "browser_search"
    params = ["query"]
    description = """
    Request to launch a browser, search a query on Google, navigate to the first search result,
    and extract the text content from that page.
    Parameters:
    - query: (required) The query to search on Google.
    Usage:
    <browser_search>
    <query>what is selenium</query>
    </browser_search>
    """
    examples = """
    Requesting to find information about Python:

    <browser_search>
    <query>official python documentation</query>
    </browser_search>
    """

    def __init__(self):
        self.driver = None
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')  # Run in headless mode - Commented out for visible browser
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu') # Optional, recommended for headless
            
            # Check for custom Chrome binary path
            chrome_binary_path = os.environ.get('CHROME_BINARY_PATH')
            if chrome_binary_path:
                options.binary_location = chrome_binary_path
            
            # Automatically download and manage ChromeDriver
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except WebDriverException as e:
            print(f"Error initializing WebDriver: {e}")
            print("Please ensure Chrome is installed and ChromeDriver is compatible or accessible.")
            # self.driver will remain None, and __call__ will handle this
        except Exception as e:
            print(f"An unexpected error occurred during WebDriver initialization: {e}")
            # self.driver will remain None

    def __call__(self, query: str):
        if not self.driver:
            return "WebDriver not initialized. Cannot perform search."

        try:
            # 1. Navigate to duckduckgo instead of Google to avoid potential issues with Google's captcha or restrictions
            self.driver.get("https://www.duckduckgo.com")

            # 2. Find search bar, enter query, and submit
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_bar.clear()
            search_bar.send_keys(query)
            search_bar.send_keys(Keys.RETURN)

            # 3. Wait for search results and find the first organic result link
            # Google's(or any other search engine's) structure can change, this selector targets common patterns for organic results
            # It looks for an h3 inside an anchor tag, within a div that typically holds a search result.
            first_result_selector = (
                "//div[@id='search']//div[contains(@class, 'g ')]//a[h3]"  # Common structure
            )
            
            try:
                first_result_link_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, first_result_selector))
                )
            except TimeoutException:
                 # Fallback selector if the primary one fails
                first_result_selector_fallback = "//div[contains(@class,'g')]//a[@href and h3]"
                try:
                    first_result_link_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, first_result_selector_fallback))
                    )
                except TimeoutException:
                    return f"Could not find the first search result link for query: '{query}' on Google."


            first_result_url = first_result_link_element.get_attribute("href")

            if not first_result_url:
                return f"Found first result element, but it has no URL for query: '{query}'"

            # 4. Navigate to the first result URL
            self.driver.get(first_result_url)

            # 5. Wait for page to load and extract text content
            # Wait for body tag to be present
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # A small delay to let dynamic content load, if any.
            # For more complex pages, more sophisticated waits might be needed.
            time.sleep(2) 
            
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            page_text = body_element.text

            # Limit the amount of text returned to keep it manageable
            max_chars = 2000
            if len(page_text) > max_chars:
                page_text = page_text[:max_chars] + "..."
            
            return f"Successfully searched for '{query}', navigated to '{first_result_url}', and extracted content: {page_text}"

        except TimeoutException:
            return f"Timeout while trying to perform search or navigate for query: '{query}'"
        except NoSuchElementException:
            return f"Could not find a required element (e.g., search bar, result link) for query: '{query}'"
        except WebDriverException as e:
            return f"WebDriver error during search for '{query}': {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred during browser operation for query '{query}': {str(e)}"

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
