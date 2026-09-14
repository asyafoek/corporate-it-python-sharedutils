from __future__ import annotations

import os
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

    @staticmethod
    def get_topic_dag_mapping() -> dict[str, str]:
        mapping = {}

        config = os.getenv("AIRFLOW_TOPIC_DAG_MAPPING", "")

        for item in config.split(";"):
            if not item.strip():
                continue

            topic, dag_id = item.split(",", 1)

            mapping[topic.strip()] = dag_id.strip()

        return mapping

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
            "logical_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "conf": {
                "key": "AAPL",
                "value": {
                    "symbol": "AAPL",
                    "price": 250.75,
                    "custom": 250.75,
                },
                "headers": {
                    "source": "simulator",
                },
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        },
    )

    print(response)


    print(client.get_topic_dag_mapping())

if __name__ == "__main__":
    main()        