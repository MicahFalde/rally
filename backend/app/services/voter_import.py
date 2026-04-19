"""Voter file import service.

Handles bulk import of state voter files using the adapter pattern.
Supports incremental updates (upsert on state_voter_id + state).
"""
import logging
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_adapter
from app.models import Voter
from app.services.geocoding import geocoding_service

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


async def import_voter_file(
    db: AsyncSession,
    file_path: str | Path,
    state_code: str,
    geocode: bool = False,
) -> dict:
    """Import a voter file for a given state.

    Args:
        db: Database session
        file_path: Path to the voter file (CSV/TSV)
        state_code: Two-letter state code
        geocode: Whether to geocode addresses via Geocodio

    Returns:
        Dict with import stats: inserted, updated, skipped, errors
    """
    adapter = get_adapter(state_code)
    records = adapter.parse_file(file_path)

    logger.info(f"Parsed {len(records)} records from {file_path}")

    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "total": len(records)}

    for batch_start in range(0, len(records), BATCH_SIZE):
        batch = records[batch_start : batch_start + BATCH_SIZE]

        # Geocode batch if requested
        if geocode:
            addresses = [
                f"{r['address_line1']}, {r['city']}, {r['state_code']} {r['zip_code']}"
                for r in batch
            ]
            geo_results = await geocoding_service.geocode_batch(addresses)

            for record, geo in zip(batch, geo_results):
                if geo:
                    record["congressional_district"] = (
                        geo.get("congressional_district")
                        or record.get("congressional_district")
                    )
                    record["state_senate_district"] = (
                        geo.get("state_senate_district")
                        or record.get("state_senate_district")
                    )
                    record["state_house_district"] = (
                        geo.get("state_house_district")
                        or record.get("state_house_district")
                    )
                    lat = geo.get("latitude")
                    lng = geo.get("longitude")
                    if lat and lng:
                        record["location"] = f"SRID=4326;POINT({lng} {lat})"

        # Upsert batch
        for record in batch:
            try:
                stmt = (
                    insert(Voter)
                    .values(**record)
                    .on_conflict_do_update(
                        index_elements=["state", "state_voter_id"],
                        set_={
                            k: v
                            for k, v in record.items()
                            if k not in ("state", "state_voter_id")
                        },
                    )
                )
                result = await db.execute(stmt)
                if result.rowcount > 0:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            except Exception as e:
                logger.error(f"Error importing voter {record.get('state_voter_id')}: {e}")
                stats["errors"] += 1

        await db.commit()
        logger.info(
            f"Processed batch {batch_start + 1}-{batch_start + len(batch)} "
            f"of {len(records)}"
        )

    return stats
