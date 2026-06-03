from extract.extract_latest import extract_latest
from extract.backfill import backfill_data
from quality.quality_checks import validate_bronze, validate_silver
from transform.transform import transform_to_silver
from transform.gold import (
    build_movement,
    build_weekly_summary,
    build_ranking,
    build_conversion,
    save_gold
)
from load.load_to_mysql import load_to_mysql

import os
import yaml
import pandas as pd
import logging


# 🔹 Setup Logging
def setup_logger():
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=f"{log_dir}/pipeline.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    return logging.getLogger()


logger = setup_logger()


def run_pipeline():

    logger.info("Pipeline started ")

    try:
        # Load config
        with open("config/config.yaml") as f:
            config = yaml.safe_load(f)

        silver_path = "data/silver/exchange_rates/exchange_rates.parquet"

        # Backfill (only first time)
        if not os.path.exists(silver_path):
            logger.info("Running backfill (first-time load)...")

            backfill_file = backfill_data()
            validate_bronze(backfill_file)

            df_backfill = transform_to_silver(backfill_file)
            validate_silver(df_backfill)

            logger.info("Backfill completed")

        # Daily Extract → Bronze
        logger.info("Running daily pipeline...")

        file_path = extract_latest()
        validate_bronze(file_path)

        # Transform → Silver
        df = transform_to_silver(file_path)
        validate_silver(df)

        logger.info("Silver layer successfully created ")

        #Load full Silver data
        df = pd.read_parquet(silver_path)
        logger.info(f"Loaded Silver data with {len(df)} records")

        # Gold Layer
        logger.info("Building Gold datasets...")

        movement = build_movement(df)
        weekly = build_weekly_summary(df)
        ranking = build_ranking(df)
        conversion = build_conversion(df)

        save_gold(movement, "movement", config)
        save_gold(weekly, "weekly_summary", config)
        save_gold(ranking, "ranking", config)
        save_gold(conversion, "conversion", config)

        logger.info("Gold layer created successfully")

        # Load to MySQL
        logger.info("Loading data into MySQL...")

        load_to_mysql()

        logger.info("Data loaded into MySQL successfully ")

        logger.info("Pipeline completed successfully ")

    except Exception as e:
        logger.error("Pipeline failed ", exc_info=True)
        print("Error occurred. Check logs.")


if __name__ == "__main__":
    run_pipeline()