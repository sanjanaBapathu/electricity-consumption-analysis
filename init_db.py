import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
database = os.getenv("DB_NAME", "electricity_analysis")
connection = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
)
cursor = connection.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS `" + database + "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE `" + database + "`")
statements = [
    "CREATE TABLE IF NOT EXISTS consumers (consumer_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(120) NOT NULL, consumer_type VARCHAR(40) NOT NULL, region VARCHAR(100) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS meters (meter_id INT AUTO_INCREMENT PRIMARY KEY, consumer_id INT NOT NULL, meter_code VARCHAR(80) NOT NULL UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (consumer_id) REFERENCES consumers(consumer_id) ON DELETE RESTRICT)",
    "CREATE TABLE IF NOT EXISTS meter_readings (reading_id INT AUTO_INCREMENT PRIMARY KEY, meter_id INT NOT NULL, reading_date DATE NOT NULL, cumulative_kwh DECIMAL(12,3) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY uq_meter_reading_date (meter_id, reading_date), CHECK (cumulative_kwh >= 0), FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT)"
]
for statement in statements:
    cursor.execute(statement)
connection.commit()
cursor.close()
connection.close()
print("Database and tables are ready.")
