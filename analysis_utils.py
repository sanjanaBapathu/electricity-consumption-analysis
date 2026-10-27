from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLUMNS = ["reading_date", "cumulative_kwh", "meter_code", "consumer_name", "region", "reading_id", "meter_id"]

def build_usage_dataframe(rows):
    df = pd.DataFrame(rows, columns=COLUMNS)
    if df.empty:
        for col in ["consumption_kwh", "validation_status", "period"]:
            df[col] = pd.Series(dtype="object")
        return df
    df["reading_date"] = pd.to_datetime(df["reading_date"])
    df["cumulative_kwh"] = pd.to_numeric(df["cumulative_kwh"], errors="coerce")
    df = df.sort_values(["meter_id", "reading_date", "reading_id"]).reset_index(drop=True)
    df["previous_kwh"] = df.groupby("meter_id")["cumulative_kwh"].shift(1)
    df["consumption_kwh"] = df["cumulative_kwh"] - df["previous_kwh"]
    df["validation_status"] = "Valid"
    df.loc[df["previous_kwh"].isna(), "validation_status"] = "First reading — no interval yet"
    df.loc[df["consumption_kwh"] < 0, "validation_status"] = "Flagged — possible reset/rollover"
    df.loc[df["validation_status"] != "Valid", "consumption_kwh"] = np.nan
    df["period"] = df["reading_date"].dt.to_period("M").astype(str)
    return df

def save_monthly_chart(monthly_df, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 4.5))
    if monthly_df.empty:
        plt.text(0.5, 0.5, "Add valid readings to display usage", ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(monthly_df["period"], monthly_df["consumption_kwh"])
        plt.title("Monthly Electricity Consumption")
        plt.xlabel("Month")
        plt.ylabel("Consumption (kWh)")
        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()
    plt.savefig(output_path, dpi=140, bbox_inches="tight")
    plt.close()
