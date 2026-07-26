import os
import time
import logging
import requests

logger = logging.getLogger("PendoTracking")

PENDO_TRACK_ENDPOINT = "https://data.pendo.io/data/track"
PENDO_INTEGRATION_KEY = os.environ.get("PENDO_INTEGRATION_KEY", "")


def pendo_track(
    event_name: str,
    properties: dict = None,
    visitor_id: str = "anonymous",
    account_id: str = "system",
):
    """Send a server-side track event to the Pendo Track API.

    Failures are logged but never propagated so tracking issues
    cannot break application flow.
    """
    if not PENDO_INTEGRATION_KEY:
        logger.debug(f"Pendo track skipped (no integration key): {event_name}")
        return

    try:
        payload = {
            "type": "track",
            "event": event_name,
            "visitorId": visitor_id,
            "accountId": account_id,
            "timestamp": int(time.time() * 1000),
            "properties": properties or {},
        }
        headers = {
            "Content-Type": "application/json",
            "x-pendo-integration-key": PENDO_INTEGRATION_KEY,
        }
        requests.post(
            PENDO_TRACK_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=5,
        )
    except Exception as e:
        logger.warning(f"Pendo track event '{event_name}' failed: {e}")
