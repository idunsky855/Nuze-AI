import asyncio
import sys
import os

import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion_service import IngestionService

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Ingestion Script")
    parser.add_argument("--dry-run", action="store_true", help="Run scrapers but skip Ollama and DB insertion")
    args = parser.parse_args()

    print(f"Starting Daily Ingest Script (Dry Run: {args.dry_run})")
    service = IngestionService()
    asyncio.run(service.run_daily_ingestion(dry_run=args.dry_run))
    print("Daily Ingest Script Finished")
