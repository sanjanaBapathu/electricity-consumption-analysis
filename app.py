import os
from datetime import date
from pathlib import Path
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from dotenv import load_dotenv
from db import get_connection
from analysis_utils import build_usage_dataframe, save_monthly_chart

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "local-dev-key-change-me")
THRESHOLD = float(os.getenv("HIGH_USAGE_THRESHOLD", "300"))
GENERATED = Path(app.root_path) / "static" / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

def query_all(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def execute(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def usage_df():
    rows = query_all("""SELECT r.reading_id, r.meter_id, r.reading_date, r.cumulative_kwh,
        m.meter_code, c.name AS consumer_name, c.region
        FROM meter_readings r JOIN meters m ON r.meter_id=m.meter_id
        JOIN consumers c ON m.consumer_id=c.consumer_id
        ORDER BY m.meter_id, r.reading_date, r.reading_id""")
    data = [(r["reading_date"], float(r["cumulative_kwh"]), r["meter_code"],
             r["consumer_name"], r["region"], r["reading_id"], r["meter_id"]) for r in rows]
    return build_usage_dataframe(data)

@app.route("/")
def dashboard():
    counts = {
        "consumers": query_all("SELECT COUNT(*) n FROM consumers")[0]["n"],
        "meters": query_all("SELECT COUNT(*) n FROM meters")[0]["n"],
        "readings": query_all("SELECT COUNT(*) n FROM meter_readings")[0]["n"],
    }
    df = usage_df()
    valid = df[df["validation_status"] == "Valid"] if not df.empty else df
    total = float(valid["consumption_kwh"].sum()) if not valid.empty else 0
    flags = int((df["validation_status"] == "Flagged — possible reset/rollover").sum()) if not df.empty else 0
    return render_template("dashboard.html", counts=counts, total=total, flags=flags, threshold=THRESHOLD)

@app.route("/consumers", methods=["GET", "POST"])
def consumers():
    if request.method == "POST":
        name, kind, region = (request.form.get(k, "").strip() for k in ("name", "consumer_type", "region"))
        if not all([name, kind, region]):
            flash("Please complete all fields.", "error")
        else:
            execute("INSERT INTO consumers (name, consumer_type, region) VALUES (%s,%s,%s)", (name, kind, region))
            flash("Consumer added.", "success")
            return redirect(url_for("consumers"))
    data = query_all("SELECT * FROM consumers ORDER BY consumer_id DESC")
    return render_template("consumers.html", consumers=data)

@app.route("/meters", methods=["GET", "POST"])
def meters():
    if request.method == "POST":
        consumer_id = request.form.get("consumer_id", type=int)
        code = request.form.get("meter_code", "").strip()
        if not consumer_id or not code:
            flash("Choose a consumer and enter a meter code.", "error")
        else:
            try:
                execute("INSERT INTO meters (consumer_id, meter_code) VALUES (%s,%s)", (consumer_id, code))
                flash("Meter added.", "success")
                return redirect(url_for("meters"))
            except Exception:
                flash("Meter could not be added. Check that its code is unique.", "error")
    consumers_list = query_all("SELECT * FROM consumers ORDER BY name")
    data = query_all("SELECT m.*, c.name consumer_name, c.region FROM meters m JOIN consumers c ON m.consumer_id=c.consumer_id ORDER BY m.meter_id DESC")
    return render_template("meters.html", meters=data, consumers=consumers_list)

@app.route("/readings", methods=["GET", "POST"])
def readings():
    if request.method == "POST":
        meter_id = request.form.get("meter_id", type=int)
        day = request.form.get("reading_date", "")
        value = request.form.get("cumulative_kwh", type=float)
        if not meter_id or not day or value is None or value < 0:
            flash("Enter a meter, date, and non-negative cumulative kWh.", "error")
        else:
            prev = query_all("SELECT reading_date, cumulative_kwh FROM meter_readings WHERE meter_id=%s ORDER BY reading_date DESC LIMIT 1", (meter_id,))
            if prev and day < str(prev[0]["reading_date"]):
                flash("Readings must be entered chronologically for each meter.", "error")
            elif prev and day == str(prev[0]["reading_date"]):
                flash("A reading already exists for this meter on that date.", "error")
            else:
                try:
                    execute("INSERT INTO meter_readings (meter_id, reading_date, cumulative_kwh) VALUES (%s,%s,%s)", (meter_id, day, value))
                    if prev and value < float(prev[0]["cumulative_kwh"]):
                        flash("Saved, but flagged for possible meter reset/rollover.", "error")
                    else:
                        flash("Reading added.", "success")
                    return redirect(url_for("readings"))
                except Exception:
                    flash("Could not save this reading. Check the details.", "error")
    meter_list = query_all("SELECT m.meter_id, m.meter_code, c.name consumer_name FROM meters m JOIN consumers c ON m.consumer_id=c.consumer_id ORDER BY c.name")
    data = query_all("SELECT r.*, m.meter_code, c.name consumer_name FROM meter_readings r JOIN meters m ON r.meter_id=m.meter_id JOIN consumers c ON m.consumer_id=c.consumer_id ORDER BY r.reading_date DESC, r.reading_id DESC")
    return render_template("readings.html", readings=data, meters=meter_list, today=date.today().isoformat())

@app.route("/reports")
def reports():
    df = usage_df()
    if df.empty:
        monthly_df = pd.DataFrame(columns=["period", "consumption_kwh"])
        monthly, yearly, validation, high_usage = [], [], [], []
    else:
        valid = df[df["validation_status"] == "Valid"].copy()
        monthly_df = valid.groupby("period", as_index=False)["consumption_kwh"].sum()
        monthly = monthly_df.to_dict("records")
        valid["year"] = valid["reading_date"].dt.year
        yearly = valid.groupby("year", as_index=False)["consumption_kwh"].sum().to_dict("records")
        validation = df[["reading_date", "consumer_name", "meter_code", "cumulative_kwh", "consumption_kwh", "validation_status"]].to_dict("records")
        high_usage = valid[valid["consumption_kwh"] > THRESHOLD][["reading_date", "consumer_name", "meter_code", "consumption_kwh"]].to_dict("records")
    save_monthly_chart(monthly_df, GENERATED / "monthly_usage.png")
    return render_template("reports.html", monthly=monthly, yearly=yearly, validation=validation, high_usage=high_usage, threshold=THRESHOLD)

@app.route("/reports/export.csv")
def export_csv():
    output = GENERATED / "consumption_report.csv"
    usage_df().to_csv(output, index=False)
    return send_file(output, as_attachment=True, download_name="consumption_report.csv", mimetype="text/csv")

if __name__ == "__main__":
    app.run(debug=True)
