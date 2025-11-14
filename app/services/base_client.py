"""Base HTTP Client with retry logic"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class BaseServiceClient:
    """Base class for microservice HTTP clients"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize service client.

        Args:
            base_url: Base URL of the microservice
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def _call_with_retry(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload (for POST/PUT)

        Returns:
            Response JSON

        Raises:
            httpx.HTTPStatusError: For non-transient errors
            httpx.TimeoutException: After all retries exhausted
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                if method.upper() == "POST":
                    response = await self.client.post(url, json=payload)
                elif method.upper() == "GET":
                    response = await self.client.get(url, params=payload)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # Transient errors - retry
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Request to {url} failed after {self.max_retries} attempts: {e}"
                    )
                    raise

                backoff = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Request to {url} failed (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {backoff}s: {e}"
                )
                await asyncio.sleep(backoff)

            except httpx.HTTPStatusError as e:
                # Check if error is transient (rate limit, server error)
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"Request to {url} failed after {self.max_retries} attempts: {e}"
                        )
                        raise

                    backoff = 2**attempt
                    logger.warning(
                        f"Request to {url} returned {e.response.status_code} "
                        f"(attempt {attempt + 1}/{self.max_retries}), retrying in {backoff}s"
                    )
                    await asyncio.sleep(backoff)
                else:
                    # Permanent error (4xx except 429) - don't retry
                    logger.error(f"Request to {url} failed with permanent error: {e}")
                    raise

    def _parse_response(self, response: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
        """
        Parse standardized microservice response.

        Expected format:
        {
            "success": true/false,
            "result": {...},
            "cost": 1.25,
            "processing_time": 3.4,
            "metadata": {...}
        }

        Args:
            response: Raw response dict

        Returns:
            Tuple of (result dict, cost float)

        Raises:
            ValueError: If response format is invalid
        """
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")

        if not response.get("success", False):
            error_msg = response.get("error", "Unknown error")
            raise ValueError(f"Service returned error: {error_msg}")

        result = response.get("result", {})
        cost = float(response.get("cost", 0.0))

        return result, cost
