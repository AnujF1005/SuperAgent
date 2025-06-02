from langchain_tavily import TavilySearch

class SearchTool:
    name = "browser_search"
    params = ["query"]
    description = """
    Request to search a query on internet.
    Parameters:
    - query: (required) The query to search on internet. 
    Usage:
    <browser_search>
    <query>search query</query>
    </browser_search>
    """
    examples = """
    Requesting to get information about how to install numpy package in conda environment

    <browser_search>
    <query>how to install numpy package in conda environment</query>
    </browser_search>
    """

    def __init__(self):
        self.search_engine = TavilySearch(
            max_results=3,
            topic="general"
        )

    def __call__(self, query: str):
        return self.search_engine(query)["results"]