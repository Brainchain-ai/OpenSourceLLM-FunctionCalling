import requests

import json, requests

class SearchServiceV2Client:
    def __init__(self, env: str = "prod", base_url: str = "https://brainchain--search-service-v2.modal.run", dev_url = "https://brainchain--search-service-v2-dev.modal.run"):
        if env == "prod":
            self.base_url = base_url
        elif env == "dev":
            self.base_url = dev_url
        else:
            raise ValueError("env must be either prod or dev")
        self.version = "v2"
        self.base_url = base_url

    def unroll_search_results(self, query):
        url = f"{self.base_url}/results"
        params = {"query": query}
        response = requests.get(url, params=params)
        return response.json()

    def shorten_link(self, link):
        url = f"{self.base_url}/shrink"
        params = {"link": link}
        response = requests.post(url, params=params)
        return response.json()

    def scanner(self, query, additional_pages=5, shorten=False):
        url = f"{self.base_url}/scanner"
        params = {
            "query": query,
            "additional_pages": additional_pages,
            "shorten": shorten
        }
        response = requests.get(url, params=params)
        return response.json()

    def basic_search(self, query, shorten = True):
        url = f"{self.base_url}/basic-search"
        params = {"query": query, shorten: shorten}
        response = requests.get(url, params=params)
        return response.json()

    def search(self, query: str):
        resp = requests.get(self.base_url + "/search" + f"?q={query}")
        jsonpayload = json.loads(resp.content)
        cached_links = jsonpayload["cached_links"] if "cached_links" in jsonpayload else None
        links = jsonpayload["links"] if "links" in jsonpayload else None
        exclusions = set([
            "hourly_forecast",
            "precipitation_forecast",
            "wind_forecast",
            "forecast",
        ])
        
        for item in [
            "rich_snippet",
            "snippet",
            "cached_links"
        ]:
            if item in list(jsonpayload.keys()):
                del jsonpayload[item]


        if "answer_box" in jsonpayload and jsonpayload["answer_box"]:
            for item in jsonpayload["answer_box"].keys():
                    if item in exclusions:
                        jsonpayload["answer_box"][item] = None
        
        return jsonpayload

    def process_webpage(self, url):
        url = f"{self.base_url}/process-webpage"
        params = {"url": url}
        response = requests.get(url, params=params)
        return response.json()

    def crawl_website(self, url, visited=None, skip_external_links=True, single_page_only=False, cached=False, model="gpt-3.5-turbo-16k"):
        url = f"{self.base_url}/crawl-website"
        params = {
            "url": url,
            "visited": visited,
            "skip_external_links": skip_external_links,
            "single_page_only": single_page_only,
            "cached": cached,
            "model": model
        }
        response = requests.get(url, params=params)
        return response.json()

# # Example usage:
# client = SearchServiceV2Client()
# response = client.basic_search("rockville temperature")
# print(response)