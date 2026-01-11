"""Mino client for browser automation via SSE streaming."""

import json
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class MinoClient:
    """Client for Mino browser automation API with SSE streaming."""

    def __init__(self, api_key: str, base_url: str = "https://mino.ai"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/v1/automation/run-sse"

    async def run_automation(
        self,
        url: str,
        goal: str,
        browser_profile: str = "lite",
        proxy_enabled: bool = False,
        proxy_country: Optional[str] = None,
    ) -> dict:
        """
        Run browser automation and collect the final result.

        Args:
            url: Target website URL to browse
            goal: Natural language task/goal description
            browser_profile: 'lite' or 'stealth'
            proxy_enabled: Whether to use proxy
            proxy_country: ISO country code for proxy

        Returns:
            dict with 'website', 'content', 'status', and optionally 'error'
        """
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        payload = {
            "url": url,
            "goal": goal,
            "browser_profile": browser_profile,
        }

        if proxy_enabled:
            payload["proxy_config"] = {
                "enabled": True,
                "country_code": proxy_country or "US",
            }

        result = {
            "website": url,
            "content": "",
            "status": "pending",
            "events": [],
        }

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 401:
                        result["status"] = "error"
                        result["error"] = "Unauthorized: Invalid or missing API key"
                        return result

                    if response.status_code != 200:
                        result["status"] = "error"
                        result["error"] = f"HTTP {response.status_code}: {await response.aread()}"
                        return result

                    # Process SSE stream
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # Log raw SSE line
                        logger.info(f"SSE: {line}")

                        # SSE format: "data: {...}"
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            if not data_str:
                                continue

                            try:
                                event = json.loads(data_str)
                                event_type = event.get("type", "")

                                result["events"].append({
                                    "type": event_type,
                                    "timestamp": event.get("timestamp"),
                                })

                                if event_type == "STARTED":
                                    result["run_id"] = event.get("runId")
                                    result["status"] = "running"

                                elif event_type == "PROGRESS":
                                    # Track progress but continue
                                    pass

                                elif event_type == "COMPLETE":
                                    status = event.get("status", "")
                                    result["status"] = status.lower()

                                    if status == "COMPLETED":
                                        result_json = event.get("resultJson", {})
                                        # Extract the content from the result
                                        if isinstance(result_json, dict):
                                            result["content"] = json.dumps(result_json, indent=2)
                                        else:
                                            result["content"] = str(result_json)
                                    else:
                                        result["error"] = f"Automation {status}"

                                elif event_type == "HEARTBEAT":
                                    # Keep-alive, ignore
                                    pass

                            except json.JSONDecodeError:
                                # Non-JSON line, skip
                                continue

        except httpx.TimeoutException:
            result["status"] = "error"
            result["error"] = "Request timed out after 300 seconds"
        except httpx.RequestError as e:
            result["status"] = "error"
            result["error"] = f"Request failed: {str(e)}"

        return result

    async def run_multiple(self, tasks: list[dict]) -> list[dict]:
        """
        Run multiple automation tasks sequentially.

        Args:
            tasks: List of dicts with 'website' and 'instructions' keys

        Returns:
            List of results from each automation run
        """
        results = []
        for task in tasks:
            result = await self.run_automation(
                url=task["website"],
                goal=task["instructions"],
            )
            results.append(result)
        return results
