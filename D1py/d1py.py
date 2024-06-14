import requests

class D1py:
    def __init__(self, account_id, api_token):
        self.account_id = account_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

    def _parse_response(self, response):
        response_json = response.json()
        result = response_json.get("result")
        success = response_json.get("success", False)
        errors = [
            {"code": error.get("code"), "message": error.get("message")}
            for error in response_json.get("errors", [])
        ]
        return {"result": result, "success": success, "errors": errors}

    def list_db(self):
        url = self.base_url
        response = requests.get(url, headers=self.headers)
        return self._parse_response(response)

    def create_db(self, db_name):
        url = self.base_url
        payload = {"name": db_name}
        response = requests.post(url, json=payload, headers=self.headers)
        return self._parse_response(response)

    def delete_db(self, db_id):
        url = f"{self.base_url}/{db_id}"
        response = requests.delete(url, headers=self.headers)
        return self._parse_response(response)

    def get_db(self, db_id):
        url = f"{self.base_url}/{db_id}"
        response = requests.get(url, headers=self.headers)
        return self._parse_response(response)

    def query_db(self, db_id, sql, params=None):
        url = f"{self.base_url}/{db_id}/query"
        payload = {
            "sql": sql,
            "params": params or []
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return self._parse_response(response)

    def raw_db_query(self, db_id, sql, params=None):
        url = f"{self.base_url}/{db_id}/raw"
        payload = {
            "sql": sql,
            "params": params or []
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return self._parse_response(response)

# Usage example:
# account_id = "your_account_id"
# api_token = "your_api_token"
# d1 = D1py(account_id, api_token)
# databases = d1.list_db()
# print(databases)