import json
import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# Bronze Validation
def validate_bronze(file_path):
    logger.info(f"Starting Bronze validation for file: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise Exception(f"File not found: {file_path}")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception:
        logger.error("Invalid JSON format in Bronze file", exc_info=True)
        raise Exception("Invalid JSON format")

    if "data" not in data:
        logger.error("Missing 'data' key in Bronze file")
        raise Exception("Missing 'data' key in Bronze file")

    api_data = data["data"]

    # Handle both latest and backfill
    if "date" in api_data:
        required_keys = ["date", "base", "rates"]
        for key in required_keys:
            if key not in api_data:
                logger.error(f"Missing key: {key}")
                raise Exception(f"Missing key: {key}")
    else:
        if "base" not in api_data or "rates" not in api_data:
            logger.error("Missing 'base' or 'rates' in backfill data")
            raise Exception("Missing 'base' or 'rates' in backfill data")

        if not isinstance(api_data["rates"], dict):
            logger.error("Invalid rates format in backfill data")
            raise Exception("Invalid rates format in backfill data")

    logger.info("Bronze validation passed ")
    return True

#  Silver Validation 
def validate_silver(df):
    logger.info("Starting Silver validation")

    # Null check
    if df[["rate_date", "base_currency", "target_currency", "exchange_rate"]].isnull().any().any():
        logger.error("Null values found in Silver data")
        raise Exception("Null values found in Silver data")

    # Positive rate check
    if (df["exchange_rate"] <= 0).any():
        logger.error("Invalid exchange rate found")
        raise Exception("Invalid exchange rate found")

    # Duplicate rows check
    if df.duplicated().any():
        logger.error("Duplicate rows found in Silver data")
        raise Exception("Duplicate rows found")

    # Business key uniqueness
    if df.duplicated(subset=["base_currency", "target_currency", "rate_date"]).any():
        logger.error("Duplicate business key found")
        raise Exception("Duplicate business key found")

    logger.info("Silver validation passed ")
    return True