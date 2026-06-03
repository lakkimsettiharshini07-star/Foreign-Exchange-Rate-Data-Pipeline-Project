import requests
import json
from datetime import datetime
import os
import yaml
import logging

logger = logging.getLogger(__name__)


def extract_latest():
    try:
        logger.info("Starting latest data extraction")

        # Load config
        with open("config/config.yaml") as f:
            config = yaml.safe_load(f)

        base = config["currency"]["base"]
        targets = ",".join(config["currency"]["targets"])

        url = f"{config['api']['url']}/latest?from={base}&to={targets}"

        logger.info(f"Calling API: {url}")

        # API call
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"API failed with status code: {response.status_code}")
            raise Exception(f"API failed: {response.status_code}")

        logger.info("API call successful")

        # Metadata
        request_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_id = f"fx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Final structure
        bronze_data = {
            "metadata": {
                "endpoint": "latest_rates",
                "request_timestamp": request_timestamp,
                "status_code": response.status_code,
                "batch_id": batch_id
            },
            "data": response.json()
        }

        # Save to Bronze
        output_path = f"{config['paths']['bronze']}/{batch_id}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(bronze_data, f, indent=4)

        logger.info(f"Bronze file saved at: {output_path}")

        return output_path

    except Exception:
        logger.error("Latest extraction failed", exc_info=True)
        raise