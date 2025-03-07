import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

def find_events_in_timeslots(date, start_time, end_time):
    """
    Find events that fit within the given date and time range by querying the database.
    
    Args:
        date: Date of the events
        start_time: Start time of the time range
        end_time: End time of the time range
    
    Returns:
        List of matching events
    """
    try:
        load_dotenv()
        
        conn = psycopg2.connect(
            dbname="xploredb",
            user="postgres", 
            password=os.getenv('DB_PASSWORD'),
            host="localhost"
        )
        cur = conn.cursor()
        
        # Query to find events within the given date and time range
        query = """
        SELECT * FROM events 
        WHERE date = '2025-02-19';
        """
        
        print(f"Querying for date: {date}, start_time: {start_time}, end_time: {end_time}")
        cur.execute(query, (date, start_time, end_time))
        matching_events = cur.fetchall()
        print(f"Found {len(matching_events)} matching events")
        
        cur.close()
        conn.close()
        
        return matching_events
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def print_events_in_timerange(start_time, end_time, events_list):
    """
    Prints all club events within the specified time range
    
    Args: 
        start_time: Start time of the time range
        end_time: End time of the time range
        events_list: List of events to print
    """
    for event in events_list:
        # Unpack tuple based on database structure
        event_id, name, description, location, date, start, end = event
        print(f"Event: {name}, Date: {date}, Start Time: {start}, End Time: {end}")




def test_time_selector_functions():
    """
    Test function for time selector functionality using database events
    """
    try:
        # Test date and time range
        date = '2024-02-17'
        start = '12:00:00'
        end = '18:00:00'

        # Get events from database
        db_events = find_events_in_timeslots(date, start, end)
        
        if not db_events:
            print("No events found in database for the specified date and time range")
            return
        else:
            print(db_events)
        

    except Exception as e:
        print(f"Error in test function: {e}")

if __name__ == "__main__":
    test_time_selector_functions()


