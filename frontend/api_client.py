import requests
from typing import Dict, Any, List

class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def login(self, email: str, password: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/auth/login", json={"email": email, "password": password})
        res.raise_for_status()
        return res.json()

    def get_financial_requests(self) -> List[Dict[str, Any]]:
        res = requests.get(f"{self.base_url}/financial-requests")
        res.raise_for_status()
        return res.json()

    def approve_target_request(self, req_id: int, note: str, user_id: int) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/financial-requests/{req_id}/approve", 
                            json={"decisionNote": note, "userId": user_id})
        res.raise_for_status()
        return res.json()

    def reject_target_request(self, req_id: int, note: str, user_id: int) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/financial-requests/{req_id}/reject", 
                            json={"decisionNote": note, "userId": user_id})
        res.raise_for_status()
        return res.json()

api_client = APIClient()
