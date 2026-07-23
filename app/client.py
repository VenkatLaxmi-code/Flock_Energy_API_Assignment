"""
client.py

The "legacy adapter" layer: everything that knows how to talk to the
Urja Meter Ops portal lives here. Nothing outside this file should ever
construct a raw httpx request to the portal directly.

Responsibilities:
- Persistent session (cookie jar) via httpx.AsyncClient
- Login + automatic re-authentication on session expiry
- Raw data fetch + normalization (DD/MM/YYYY -> datetime, strings -> floats)
- Retry logic for transient network failures
- Clear, typed exceptions for callers (FastAPI layer) to translate into
  HTTP status codes
"""

import asyncio
import json 
from datetime import datetime
from typing import Any, Optional

import httpx


from app.config import settings


class UrjaAuthError(Exception):
    """Raised when login to the legacy portal fails (bad credentials, portal down, etc.)."""


class UrjaNotFoundError(Exception):
    """Raised when a requested meter ID does not exist."""


class UrjaUpstreamError(Exception):
    """Raised for unexpected upstream failures (network, 5xx, malformed data)."""


class UrjaClient:
    """
    Async client wrapping the legacy Urja Meter Ops portal.

    Usage:
        client = UrjaClient()
        await client.login()
        meters = await client.get_meters(page=1)
        await client.close()
    """

    def __init__(self) -> None:
        self.base_url = settings.urja_base_url
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
        )
        self._logged_in_at: Optional[datetime] = None

    async def close(self) -> None:
        await self._http.aclose()

    @property
    def is_authenticated(self) -> bool:
        return self._logged_in_at is not None

    @property
    def logged_in_at(self) -> Optional[datetime]:
        return self._logged_in_at

    # ---------------- Authentication ----------------

    async def login(self) -> None:
        """
        Logs into the legacy portal using credentials from settings.
        """
        try:
            response = await self._http.post(
                "/login",
                data={
                    "email": settings.urja_email,
                    "password": settings.urja_password,
                },
                headers={
                    "Accept": "application/json",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/login",
                    "x-sveltekit-action": "true",
                },
            )
        except httpx.RequestError as exc:
            raise UrjaUpstreamError(
                f"Network error while logging in: {exc}"
            ) from exc

        
        if response.status_code >= 400:
            raise UrjaAuthError(
                f"Login failed. Status={response.status_code}, Body={response.text}"
            )

        try:
            payload = response.json()

            if (
                payload.get("type") == "redirect"
                and payload.get("location") == "/meters"
            ):
                self._logged_in_at = datetime.utcnow()
                return
        except Exception:
            pass

        if "/login" in str(response.url):
            raise UrjaAuthError("Login failed.")

        self._logged_in_at = datetime.utcnow()
    async def _request_with_reauth(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Makes a request. If the response indicates the session has expired
        (redirected to /login, or 401/403), transparently re-authenticates
        once and retries the original request.

        This is the reactive re-auth strategy: rather than guessing a cookie
        TTL, we let the server tell us when we're no longer authenticated.
        """
        response = await self._safe_request(method, url, **kwargs)

        session_expired = (
            "/login" in str(response.url) or response.status_code in (401, 403)
        )
        if session_expired:
            await self.login()
            response = await self._safe_request(method, url, **kwargs)

            still_expired = (
                "/login" in str(response.url) or response.status_code in (401, 403)
            )
            if still_expired:
                raise UrjaAuthError(
                    "Re-authentication failed; portal still rejecting the session."
                )

        return response

    async def _safe_request(self, method: str, url: str, retries: int = 2, **kwargs) -> httpx.Response:
        """
        Low-level request wrapper with a small retry loop for transient
        network failures (timeouts, connection resets). Does NOT retry on
        4xx/5xx HTTP responses -- only on actual network-level errors.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                return await self._http.request(method, url, **kwargs)
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))  # simple backoff
                    continue
        raise UrjaUpstreamError(f"Network error calling {url}: {last_exc}") from last_exc

    # ---------------- Data endpoints ----------------

    async def get_meters(self, page: int = 1, q: str = "") -> dict[str, Any]:
        response = await self._request_with_reauth(
            "GET", "/portal/meters/search", params={"q": q, "page": page}
        )
        if response.status_code != 200:
            raise UrjaUpstreamError(
                f"Unexpected status {response.status_code} from meters search"
            )
        return response.json()

    async def get_meter_by_id(self, meter_id: str) -> Optional[dict[str, Any]]:
        """
        The legacy portal has no dedicated single-meter endpoint, so we
        reuse the search endpoint (confirmed during investigation to do
        exact filtering server-side) and take the first match.
        """
        payload = await self.get_meters(page=1, q=meter_id)
        matches = payload.get("data", [])
        if not matches:
            return None
        return matches[0]

    async def get_energy(self, meter_id: str) -> list[dict[str, Any]]:
        response = await self._request_with_reauth(
            "GET", f"/portal/meters/{meter_id}/energy"
        )
        if response.status_code == 404:
            raise UrjaNotFoundError(f"Meter '{meter_id}' not found")
        if response.status_code != 200:
            raise UrjaUpstreamError(
                f"Unexpected status {response.status_code} from energy endpoint"
            )
        return response.json().get("data", [])

    async def get_geo(self, meter_id: str) -> Optional[dict[str, Any]]:
        response = await self._request_with_reauth(
            "GET", f"/portal/meters/{meter_id}/geo"
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise UrjaUpstreamError(
                f"Unexpected status {response.status_code} from geo endpoint"
            )
        return response.json().get("data")


# A single shared client instance used across the FastAPI app's lifetime.
urja_client = UrjaClient()