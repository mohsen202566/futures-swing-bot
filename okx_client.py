from __future__ import annotations
from typing import Any
import requests, config
class OKXError(RuntimeError): pass
class OKXClient:
    def __init__(self, base_url: str = config.OKX_BASE_URL, timeout: int = config.REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip('/'); self.timeout = timeout; self.session = requests.Session()
    def get(self, path: str, params: dict[str,Any] | None = None) -> Any:
        try:
            r = self.session.get(f'{self.base_url}{path}', params=params or {}, timeout=self.timeout)
            if r.status_code >= 400: raise OKXError(f'HTTP {r.status_code}: {r.text[:300]}')
            payload = r.json()
        except Exception as exc:
            if isinstance(exc, OKXError): raise
            raise OKXError(f'خطا در ارتباط با OKX: {exc}') from exc
        if isinstance(payload, dict) and str(payload.get('code','0')) not in {'0','200'}: raise OKXError(f'پاسخ ناموفق OKX: {payload}')
        return payload
