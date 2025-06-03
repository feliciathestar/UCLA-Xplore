# used to insert data into the events table in the postgres database 

import pandas as pd
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
print("Loading environment variables...")
load_dotenv()

# Load the CSV file
file_path = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/scripts/2025spring_events.csv" 
print(f"Loading CSV file from {file_path}...")
df = pd.read_csv(file_path)
print(f"CSV file loaded successfully. Number of rows: {len(df)}")

###### for connecting to Aiven PostgreSQL ######
# Aiven PostgreSQL connection details from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "25829")  # Default to 5432 if not specified

print("Connecting to Aiven PostgreSQL...")
# Connect to Aiven PostgreSQL with SSL
conn = psycopg2.connect(
    dbname=DB_NAME, 
    user=DB_USER, 
    password=DB_PASSWORD, 
    host=DB_HOST, 
    port=DB_PORT,
    sslmode='require'  # Required for Aiven
)
print("Connection established successfully.")
cursor = conn.cursor()

# # Clear existing data from the events table
# print("Clearing existing data from the events table...")
# cursor.execute("DELETE FROM events;")
# conn.commit()  # Commit the deletion
# print("Existing data cleared.")

# # Add the event_link column to the events table
# print("Adding event_link column to the events table...")
# cursor.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_link TEXT;")
# conn.commit()  # Commit the schema change
# print("event_link column added successfully.")

# Insert data into events table
print("Inserting data into the events table...")
for index, row in df.iterrows():
    print(f"Inserting row {index + 1}...")
    cursor.execute(
        """
        INSERT INTO events (event_name, event_description, event_location, date, start_time, end_time, event_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (row["event_name"], row["event_description"], row["event_location"], row["date"], row["start_time"], row["end_time"], row["event_link"])
    )
print("All rows inserted successfully.")

# Commit and close connection
print("Committing changes and closing the connection...")
conn.commit()
cursor.close()
conn.close()
print("Connection closed.")

print("Data successfully inserted into Aiven PostgreSQL!")
