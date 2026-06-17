#!/usr/bin/env python3
"""Sync event sources from cron or manual ops.

Modes:
  cinema — Kinopskov, Mirage, Silver, Orbilet + enrichment + cinema monitor
  all    — all configured sources + enrichment + cinema monitor
  enrich — re-enrich genres/posters only (no external fetch)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.cinema_monitor import check_cinema_block_and_alert
from app.services.event_enrichment_batch import enrich_missing_posters, enrich_stale_events
from app.services.event_source_health import build_event_sources_health
from app.services.event_sources.coordinator import sync_all_event_sources, sync_cinema_event_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_all_events")


def _summarize_results(results) -> dict[str, object]:
    return {
        "sources": len(results),
        "created": sum(r.created for r in results),
        "updated": sum(r.updated for r in results),
        "skipped": sum(r.skipped for r in results),
        "errors": [e for r in results for e in r.errors],
    }


async def run(mode: str, *, notify: bool) -> int:
    settings = get_settings()
    health = build_event_sources_health()
    logger.info("Event source health: %s", json.dumps(health, ensure_ascii=False))
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        if mode == "enrich":
            updated = await enrich_stale_events(db)
            posters = await enrich_missing_posters(db, limit=80)
            await db.commit()
            logger.info("Enriched %s events, posters %s", updated, posters)
        elif mode == "cinema":
            results = await sync_cinema_event_sources(db)
            await db.commit()
            summary = _summarize_results(results)
            logger.info("Cinema sync: %s", json.dumps(summary, ensure_ascii=False))
            if summary["errors"]:
                for err in summary["errors"]:
                    logger.error("Source error: %s", err)
        else:
            results = await sync_all_event_sources(db)
            await db.commit()
            summary = _summarize_results(results)
            logger.info("Full sync: %s", json.dumps(summary, ensure_ascii=False))
            if summary["errors"]:
                for err in summary["errors"]:
                    logger.error("Source error: %s", err)

        monitor = await check_cinema_block_and_alert(db, notify=notify)
        print(json.dumps({"mode": mode, "monitor": monitor}, ensure_ascii=False))

    await engine.dispose()
    return 0 if monitor.get("ok") else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync PGBot event sources")
    parser.add_argument(
        "--mode",
        choices=("cinema", "all", "enrich"),
        default="cinema",
        help="cinema=afisha sources; all=every source; enrich=metadata only",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Skip Telegram/VK alert when cinema block is empty",
    )
    args = parser.parse_args()
    exit_code = asyncio.run(run(args.mode, notify=not args.no_notify))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
