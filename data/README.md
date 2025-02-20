# Setting Up PostgreSQL


## Description
Follow this guide to set up postgres locally and populate local tables with sample events from UCLA Winter Week7.

## Download PostgreSQL

Make sure you have the following installed on your local machine:

- PostgreSQL (Ensure psql is accessible from the terminal), https://www.postgresql.org/download/

- A database on PostgreSQL created to store the tables

## Connect to PostgreSQL

1. Open a terminal or command prompt.

2. Start a PostgreSQL session by running:
```
$ psql -U <your_username> -d <your_database>
```

## Create the events & timeslotsTable
Run the following SQL command to create the events table:
     
```
psql=# CREATE TABLE events (
       event_id SERIAL PRIMARY KEY,
       event_name VARCHAR(255) NOT NULL,
       event_description TEXT,
       event_location VARCHAR(255),
       date DATE NOT NULL,
       start_time TIME WITHOUT TIME ZONE NOT NULL,
       end_time TIME WITHOUT TIME ZONE NOT NULL
       );
```
```
psql=# CREATE TABLE timeslots (
       slot_id SERIAL PRIMARY KEY,
       event_id JSONB NOT NULL,
       date DATE NOT NULL,
       start_time TIME WITHOUT TIME ZONE NOT NULL,
       end_time TIME WITHOUT TIME ZONE NOT NULL
       );
```         
            
## Verify Table Creation

1. After running the SQL commands, confirm the tables exist by running:

```
psql=# \dt
```
You should see events and timeslots listed.


2. To check their structure, run:
```
psql=# \d events
```
```
psql=# \d timeslots
```

## Populate Timeslots Table

1. Insert all time slots (30 mins interval) between date 2025-02-17 and 2025-02-25
```
psql=# INSERT INTO timeslots (date, start_time, end_time)
       SELECT 
           d.date,
           (make_time(0,0,0) + (n - 1) * interval '30 minutes')::time AS start_time,
           (make_time(0,0,0) + (n - 1) * interval '30 minutes' + interval '30 minutes')::time AS end_time
       FROM (
           SELECT ('2025-02-17'::date + INTERVAL '1 day' * (a.a + (10 * b.a))) AS date
           FROM (SELECT 0 a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 
               UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a
           CROSS JOIN (SELECT 0 a UNION ALL SELECT 1) b
           WHERE ('2025-02-17'::date + INTERVAL '1 day' * (a.a + (10 * b.a))) <= '2025-02-25'
       ) d
       CROSS JOIN generate_series(1, 48) n;
```

2. Check the First Few Rows
```
psql=# SELECT * FROM timeslots LIMIT 10;
```

3. Check the Total Number of Inserted Rows
```
psql=# SELECT COUNT(*) FROM timeslots;
```

## Insert Sample Data into Events Table

Run insert_events.py (/Users/wanxinxiao/Desktop/UCLA-Xplore/data/scripts/insert_events.py) to transfer all rows in the excel sheet to events table.
Remeber to install the required package:
```
$ pip3 install psycopg2
```

## Linking event_id's to time slots in Timeslots Table

```
psql=# UPDATE timeslots ts
       SET ts.event_id = COALESCE(ts.event_id, '[]'::JSONB) || to_jsonb(e.event_id)
       FROM events e
       WHERE ts.date = e.date
       AND ts.start_time >= e.start_time 
       AND ts.start_time < e.end_time;
```

## Querying Tables

Query all event_ids for your selected time slots:

```
psql=# SELECT DISTINCT jsonb_array_elements(event_id) AS event_id
       FROM timeslots
       WHERE date = '2025-02-18'
       AND start_time IN ('10:00:00', '10:30:00', '11:00:00', '11:30:00');

```
