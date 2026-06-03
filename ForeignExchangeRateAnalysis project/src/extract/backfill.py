import requests
import json
from datetime import datetime, timedelta
import os
import yaml
import logging

logger = logging.getLogger(__name__)


def backfill_data():
    try:
        logger.info("Starting backfill process (last 30 days)")

        # Load config
        with open("config/config.yaml") as f:
            config = yaml.safe_load(f)

        base = config["currency"]["base"]
        targets = ",".join(config["currency"]["targets"])

        # Date range
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=30)

        logger.info(f"Fetching data from {start_date} to {end_date}")

        # API URL
        url = f"{config['api']['url']}/{start_date}..{end_date}?from={base}&to={targets}"

        # API call
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"API call failed with status {response.status_code}")
            raise Exception(f"API failed: {response.status_code}")

        logger.info("API call successful ")

        # Metadata
        metadata = {
            "endpoint": "backfill",
            "request_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_code": response.status_code,
            "batch_id": f"fx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        # Combine data
        bronze_data = {
            "metadata": metadata,
            "data": response.json()
        }

        # Save to Bronze
        output_path = f"{config['paths']['bronze']}/{metadata['batch_id']}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(bronze_data, f, indent=4)

        logger.info(f"Backfill saved at: {output_path}")

        return output_path

    except Exception:
        logger.error("Backfill process failed", exc_info=True)
        raise