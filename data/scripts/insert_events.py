# used to insert data into the events table in the postgres database 

import pandas as pd
import psycopg2
from datetime import datetime

# Load the Excel file
file_path = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/raw/events_calendar/w07_processed.xlsx"  # Update the path if necessary
df = pd.read_excel(file_path)


###### for connecting to postgres locally ######

# PostgreSQL connection details
DB_NAME = "event_scheduler"
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()


# Insert data into events table
for _, row in df.iterrows():
    cursor.execute(
        """
        INSERT INTO events (event_name, event_description, event_location, date, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (row["event_name"], row["event_description"], row["event_location"], row["date"], row["start_time"], row["end_time"])
    )

# Commit and close connection
conn.commit()
cursor.close()
conn.close()

print("Data successfully inserted into PostgreSQL!")
