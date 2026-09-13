from __future__ import annotations

from datetime import datetime, timezone
import requests



class AirflowApiClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

        self._token: str | None = None

    def authenticate(self) -> str:
        response = requests.post(
            f"{self.base_url}/auth/token",
            json={
                "username": self.username,
                "password": self.password,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        self._token = response.json()["access_token"]
        return self._token

    @property
    def token(self) -> str:
        if not self._token:
            self.authenticate()

        return self._token

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        **kwargs,
    ):
        response = requests.request(
            method=method.upper(),
            url=f"{self.base_url}{path}",
            headers=self.headers,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()

        if response.content:
            return response.json()

        return None

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)


def main():
    client = AirflowApiClient(
        base_url="http://localhost:8080",
        username="admin",
        password="admin",
    )

    dags = client.get("/api/v2/dags")
    for dag in dags.get("dags", []):
        print(dag["dag_id"])

    response = client.post(
        "/api/v2/dags/corporate_it_idts_process_kafka_message_manually/dagRuns",
        json={
            "conf": {
                "key": "AAPL",
                "value": {
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 100,
                    "price": 250.75,
                },
                "headers": {
                    "source": "simulator",
                    "topic": "stock-orders",
                    "event_type": "order_created",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    print(response)

if __name__ == "__main__":
    main()        