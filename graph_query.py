import requests

class GraphQueryClient:
    def __init__(self):
        self.base_url = "https://brainchain--graph-query.modal.run"

    def get_root(self):
        response = requests.get(f"{self.base_url}/")
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()

    def refresh_schema(self) -> dict:
        response = requests.post(f"{self.base_url}/refresh-schema")
        response.raise_for_status()
        return response.json()

    def get_schema(self) -> dict:
        response = requests.get(f"{self.base_url}/schema")
        response.raise_for_status()
        return response.json()

    def graph_query(self, question, results=25, model="gpt-4-32k", temperature=0.0, max_tokens=16384):
        payload = {
            "question": question,
            "results": results,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{self.base_url}/graph-query", json=payload, headers=headers)
        return response.json()

    def handle_error(self, response):
        # Custom error handling could go here
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 422:
                # Handle the validation error as per API specification
                error_details = response.json()
                return error_details
            else:
                raise
