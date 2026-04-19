"""Geocoding service using Geocodio API.

Geocodio returns lat/lon plus legislative district assignments in one call.
Pricing: ~$0.50 per 1,000 lookups. Batch endpoint handles up to 10,000 per request.
"""
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEOCODIO_BASE = "https://api.geocod.io/v1.7"


class GeocodingService:
    def __init__(self):
        self.api_key = settings.geocodio_api_key

    async def geocode_single(self, address: str) -> dict | None:
        """Geocode a single address and return location + districts."""
        if not self.api_key:
            logger.warning("No Geocodio API key configured")
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GEOCODIO_BASE}/geocode",
                params={
                    "q": address,
                    "fields": "cd,stateleg",
                    "api_key": self.api_key,
                },
            )
            if resp.status_code != 200:
                logger.error(f"Geocodio error: {resp.status_code} {resp.text}")
                return None

            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

            top = results[0]
            location = top.get("location", {})
            fields = top.get("fields", {})

            return {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "congressional_district": self._extract_cd(fields),
                "state_senate_district": self._extract_state_leg(fields, "senate"),
                "state_house_district": self._extract_state_leg(fields, "house"),
            }

    async def geocode_batch(self, addresses: list[str]) -> list[dict | None]:
        """Geocode up to 10,000 addresses in one API call.

        Returns a list of results in the same order as input.
        """
        if not self.api_key:
            logger.warning("No Geocodio API key configured")
            return [None] * len(addresses)

        results = []

        # Geocodio batch limit is 10,000 per request
        for chunk_start in range(0, len(addresses), 10000):
            chunk = addresses[chunk_start : chunk_start + 10000]

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{GEOCODIO_BASE}/geocode",
                    params={
                        "fields": "cd,stateleg",
                        "api_key": self.api_key,
                    },
                    json=chunk,
                )

                if resp.status_code != 200:
                    logger.error(f"Geocodio batch error: {resp.status_code} {resp.text}")
                    results.extend([None] * len(chunk))
                    continue

                data = resp.json()
                batch_results = data.get("results", [])

                for item in batch_results:
                    response = item.get("response", {})
                    geo_results = response.get("results", [])
                    if not geo_results:
                        results.append(None)
                        continue

                    top = geo_results[0]
                    location = top.get("location", {})
                    fields = top.get("fields", {})

                    results.append({
                        "latitude": location.get("lat"),
                        "longitude": location.get("lng"),
                        "congressional_district": self._extract_cd(fields),
                        "state_senate_district": self._extract_state_leg(fields, "senate"),
                        "state_house_district": self._extract_state_leg(fields, "house"),
                    })

        return results

    def _extract_cd(self, fields: dict) -> str | None:
        cd = fields.get("congressional_districts", [])
        if cd:
            district = cd[0]
            name = district.get("name", "")
            return name if name else None
        return None

    def _extract_state_leg(self, fields: dict, chamber: str) -> str | None:
        state_leg = fields.get("state_legislative_districts", {})
        chamber_data = state_leg.get(chamber, [])
        if chamber_data:
            district = chamber_data[0]
            name = district.get("name", "")
            return name if name else None
        return None


geocoding_service = GeocodingService()
