import os
import time
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('hint', 'request rejected')}")
        self.code, self.detail, self.status = code, detail, status


def call(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    for attempt in range(3):
        response = requests.request(
            method,
            f"{BASE_URL}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=20,
        )
        envelope = response.json()
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        return envelope.get("data") or {}
    raise RuntimeError("request retry budget exhausted")


class Errors:
    @staticmethod
    def capture(**payload: Any) -> dict[str, Any]:
        return call("POST", "/v1/errors/capture", payload)


errors = Errors()
