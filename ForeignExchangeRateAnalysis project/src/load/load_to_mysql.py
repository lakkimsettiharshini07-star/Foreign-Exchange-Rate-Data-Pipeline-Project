import mysql.connector
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_to_mysql():

    try:
        logger.info("Connecting to MySQL database...")

        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Harshi@2780",  
            database="fx_pipeline"
        )

        cursor = conn.cursor()
        logger.info("Connection successful ")

        # Load Gold data
        logger.info("Loading Gold datasets from parquet...")

        movement = pd.read_parquet("data/gold/marts/movement.parquet")
        weekly = pd.read_parquet("data/gold/marts/weekly_summary.parquet")
        ranking = pd.read_parquet("data/gold/marts/ranking.parquet")
        conversion = pd.read_parquet("data/gold/marts/conversion.parquet")

        logger.info("Gold datasets loaded successfully")

        # Create tables
        logger.info("Creating tables if not exist")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_movement (
            rate_date DATE,
            base_currency VARCHAR(10),
            target_currency VARCHAR(10),
            exchange_rate FLOAT,
            prev_rate FLOAT,
            change_rate FLOAT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_weekly_summary (
            target_currency VARCHAR(10),
            avg_7_day_rate FLOAT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_ranking (
            rate_date DATE,
            base_currency VARCHAR(10),
            target_currency VARCHAR(10),
            exchange_rate FLOAT,
            rank_num INT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_conversion (
            base_currency VARCHAR(10),
            target_currency VARCHAR(10),
            exchange_rate FLOAT
        )
        """)

        cursor.execute("DELETE FROM gold_movement")
        cursor.execute("DELETE FROM gold_weekly_summary")
        cursor.execute("DELETE FROM gold_ranking")
        cursor.execute("DELETE FROM gold_conversion")

        # Insert data
        logger.info("Inserting data into tables...")

        movement = movement.where(pd.notnull(movement), None)
        weekly = weekly.where(pd.notnull(weekly), None)
        ranking = ranking.where(pd.notnull(ranking), None)
        conversion = conversion.where(pd.notnull(conversion), None)

        # Movement
        for _, row in movement.iterrows():

            prev_rate = None if pd.isna(row["prev_rate"]) else float(row["prev_rate"])
            change = None if pd.isna(row["change"]) else float(row["change"])

            cursor.execute("""
            INSERT INTO gold_movement VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row["rate_date"],
                row["base_currency"],
                row["target_currency"],
                float(row["exchange_rate"]),
                prev_rate,
                change
            ))

        logger.info(f"Inserted {len(movement)} rows into gold_movement")

        # Weekly
        for _, row in weekly.iterrows():
            cursor.execute("""
            INSERT INTO gold_weekly_summary VALUES (%s, %s)
            """, (
                row["target_currency"],
                row["avg_7_day_rate"]
            ))

        logger.info(f"Inserted {len(weekly)} rows into gold_weekly_summary")

        # Ranking
        for _, row in ranking.iterrows():
            cursor.execute("""
            INSERT INTO gold_ranking VALUES (%s, %s, %s, %s, %s)
            """, (
                row["rate_date"],
                row["base_currency"],
                row["target_currency"],
                row["exchange_rate"],
                row["rank"]
            ))

        logger.info(f"Inserted {len(ranking)} rows into gold_ranking")

        # Conversion
        for _, row in conversion.iterrows():
            cursor.execute("""
            INSERT INTO gold_conversion VALUES (%s, %s, %s)
            """, (
                row["base_currency"],
                row["target_currency"],
                row["exchange_rate"]
            ))

        logger.info(f"Inserted {len(conversion)} rows into gold_conversion")

        conn.commit()
        conn.close()

        logger.info("Data loaded into MySQL successfully ")

    except Exception as e:
        logger.error("Error while loading data into MySQL ", exc_info=True)
        raise