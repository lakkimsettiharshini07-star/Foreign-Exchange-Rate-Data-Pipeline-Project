import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

#moments
def build_movement(df):
    logger.info("Building movement dataset")

    df = df.sort_values(["target_currency", "rate_date"])
    df["prev_rate"] = df.groupby("target_currency")["exchange_rate"].shift(1)
    df["change"] = df["exchange_rate"] - df["prev_rate"]

    logger.info(f"Movement dataset created with {len(df)} rows")

    return df


# 2️ Weekly Summary
def build_weekly_summary(df):
    logger.info("Building weekly summary dataset")

    last_7_days = df[df["rate_date"] >= df["rate_date"].max() - pd.Timedelta(days=7)]

    summary = last_7_days.groupby("target_currency")["exchange_rate"].mean().reset_index()
    summary.rename(columns={"exchange_rate": "avg_7_day_rate"}, inplace=True)

    logger.info(f"Weekly summary created with {len(summary)} rows")

    return summary

# 3️ Ranking
def build_ranking(df):
    logger.info("Building ranking dataset")

    latest_date = df["rate_date"].max()
    latest_df = df[df["rate_date"] == latest_date]

    ranking = latest_df.sort_values("exchange_rate", ascending=False)
    ranking["rank"] = range(1, len(ranking) + 1)

    logger.info(f"Ranking created for {len(ranking)} currencies")

    return ranking

# 4️ Conversion
def build_conversion(df):
    logger.info("Building conversion dataset")

    latest_date = df["rate_date"].max()

    conversion = df[df["rate_date"] == latest_date][
        ["base_currency", "target_currency", "exchange_rate"]
    ]

    logger.info(f"Conversion dataset created with {len(conversion)} rows")

    return conversion


# Save function
def save_gold(df, name, config):
    try:
        output_path = f"{config['paths']['gold']}/{name}.parquet"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        df.to_parquet(output_path, index=False)

        logger.info(f"{name} saved at {output_path} ")

    except Exception as e:
        logger.error(f"Error saving {name} ", exc_info=True)
        raise