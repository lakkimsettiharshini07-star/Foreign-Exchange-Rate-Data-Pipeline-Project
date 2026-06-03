import json
import pandas as pd
import os
import yaml
import logging


logger = logging.getLogger(__name__)


def transform_to_silver(bronze_file_path):

    logger.info(f"Starting transformation for file: {bronze_file_path}")

    # Load config
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    # Read Bronze file
    try:
        with open(bronze_file_path, "r") as f:
            bronze_data = json.load(f)
    except Exception:
        logger.error("Error reading Bronze file", exc_info=True)
        raise

    data = bronze_data["data"]
    metadata = bronze_data["metadata"]

    base_currency = data["base"]
    ingestion_time = metadata["request_timestamp"]
    batch_id = metadata["batch_id"]

    records = []

    # 🔹 Handle Latest API
    if "date" in data:
        logger.info("Processing latest API data")

        rate_date = data["date"]
        for target_currency, exchange_rate in data["rates"].items():
            records.append({
                "rate_date": rate_date,
                "base_currency": base_currency,
                "target_currency": target_currency,
                "exchange_rate": exchange_rate,
                "ingestion_time": ingestion_time,
                "batch_id": batch_id
            })

    # 🔹 Handle Backfill API
    else:
        logger.info("Processing backfill API data")

        for rate_date, daily_rates in data["rates"].items():
            for target_currency, exchange_rate in daily_rates.items():
                records.append({
                    "rate_date": rate_date,
                    "base_currency": base_currency,
                    "target_currency": target_currency,
                    "exchange_rate": exchange_rate,
                    "ingestion_time": ingestion_time,
                    "batch_id": batch_id
                })

    logger.info(f"Total records created: {len(records)}")

    # Create DataFrame
    df = pd.DataFrame(records)

    # Data cleaning
    df["rate_date"] = pd.to_datetime(df["rate_date"])
    df["exchange_rate"] = pd.to_numeric(df["exchange_rate"])

    logger.info("Data cleaning completed")

    # Save to Silver 
    output_path = f"{config['paths']['silver']}/exchange_rates.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Append with existing data
    if os.path.exists(output_path):
        logger.info("Existing Silver file found → appending data")

        existing_df = pd.read_parquet(output_path)
        before_count = len(existing_df)

        df = pd.concat([existing_df, df], ignore_index=True)

        logger.info(f"Rows before append: {before_count}, after append: {len(df)}")

    # REMOVE DUPLICATES 
    before_dedup = len(df)
    df = df.drop_duplicates(
        subset=["base_currency", "target_currency", "rate_date"],
        keep="last"
    )
    after_dedup = len(df)

    logger.info(f"Duplicates removed: {before_dedup - after_dedup}")

    # Save
    df.to_parquet(output_path, index=False)

    logger.info(f"Saved Silver data at: {output_path}")

    return df