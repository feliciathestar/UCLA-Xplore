# use this to process the raw data from the events calendar amd sort them into the correct columns into csv

import pandas as pd
import re
from datetime import datetime, date, timedelta

# assign data to be processed (a week in a quarter)
file_path= "raw/events_calendar/w08.txt"

def convert_time(time_str, all_day, is_start_time=False):
    """Convert time to PostgreSQL format
    Args:
        time_str: The time string to convert
        all_day: "T" if all-day event, "F" otherwise
        is_start_time: True if converting start time, False if end time
    """
    if all_day == "T":
        return "00:00:00" if is_start_time else "23:59:59"
    
    if pd.isna(time_str):
        return None
        
    try:
        try:
            return datetime.strptime(str(time_str), "%I%p").strftime("%H:%M:%S")
        except ValueError:
            return datetime.strptime(str(time_str), "%I:%M%p").strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return time_str

def parse_raw_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        raw_content = file.readlines()
    
    events = []
    current_event = None
    event_start_lines = {}
    # Initialize current_event at the start of the function
    current_event = {
        "event_name": None,
        "event_info_link": None,
        "event_tags": None,
        "event_programe": None,
        "date": None,
        "start_time": "00:00:00",
        "all_day": "T",
        "end_time": None,
        "event_description": None,
        "event_location": None,
    }
    
    for i, line in enumerate(raw_content):
        line = line.strip()
        
        # Check if the line is a new event
        event_match = re.match(r'### \[(.*?)\]\((.*?)\)', line)
        # If it is an event
        if event_match:

            # Save the previous event if exists
            if current_event:
                events.append(current_event)
            
            # Reset event storage
            current_event = {
                "event_name": event_match.group(1),
                "event_info_link": event_match.group(2),
                "event_tags": None,
                "event_programe": None,
                "date": None,
                "start_time": "00:00:00",
                "all_day": "T",
                "end_time": None,
                "event_description": None,
                "event_location": None,
            }
            event_start_lines[event_match.group(1)] = i
            continue

        # Extract date (format like "Mon 2/17")
        date_match = re.search(r'([A-Za-z]+) (\d+)/(\d+)', line)
        if date_match:
            month, day = int(date_match.group(2)), int(date_match.group(3))
            date_obj = date(2025, month, day)
            current_event["date"] = date_obj.strftime('%Y-%m-%d')

        # Extract time 
        def parse_time(time_str):
            """Convert time string like '1PM' or '12:30PM' to datetime"""
            try:
                return datetime.strptime(time_str.strip(), '%I:%M%p')
            except ValueError:
                return datetime.strptime(time_str.strip(), '%I%p')

        # (format like "1PM - 3PM PST") 
        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s?(?:AM|PM))(?:\s*-\s*(\d{1,2}(?::\d{2})?\s?(?:AM|PM)))?\s*(?:PST)?', line)
        if time_match:
            start_time = time_match.group(1)
            current_event["start_time"] = start_time
            # current_event["end_time"] = time_match.group(2) if time_match.group(2) else None
            if time_match.group(2):  # If end time is provided
                current_event["end_time"] = time_match.group(2)
            else:  # Calculate end time as start time + 2 hours
                start_dt = parse_time(start_time)
                end_dt = start_dt + timedelta(hours=2)
                current_event["end_time"] = end_dt.strftime("%I:%M%p")
            current_event["all_day"] = "F" # Set all_day to False since we have a specific time
        
        # Match the categories
        category_match = re.findall(r'\[(.*?)\]\(.*?"(.*?)"\)', line)
        if category_match:
            current_event["event_programe"] = ", ".join([cat[1] for cat in category_match])
            continue
        
        # Match the tags
        tag_match = re.findall(r'\[(.*?)\]', line)
        if tag_match and not re.findall(r'\[(.*?)\]\(.*?"(.*?)"\)', line):
            current_event["event_tags"] = ", ".join(tag_match)
            continue
    
    for event in events:
        start_line = event_start_lines.get(event["event_name"], -1)
        
        if start_line != -1:
            location_line = start_line + 4
            if location_line < len(raw_content):
                event["event_location"] = raw_content[location_line].strip()
            
            description_line = start_line + 6
            if description_line < len(raw_content):
                event["event_description"] = raw_content[description_line].strip()
    
    # Convert DataFrame and normalize formats
    df = pd.DataFrame(events)
    
    # Shift dates down by one row
    df['date'] = df['date'].shift(1)
    
    # Convert to datetime after shifting
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    # Handle time columns with None values
    df["start_time"] = df.apply(lambda row: convert_time(row["start_time"], row["all_day"], is_start_time=True), axis=1)
    df["end_time"] = df.apply(lambda row: convert_time(row["end_time"], row["all_day"], is_start_time=False), axis=1)
    
    return df

def classify_and_save_w07(path_to_raw, path_example_columns, output_path):
    events_df = parse_raw_txt(path_to_raw)
    
    book1_xl = pd.ExcelFile(path_example_columns)
    sheet_name = book1_xl.sheet_names[0]
    book1_df = book1_xl.parse(sheet_name)
    
    # Ensure book1_df has same date/time format
    book1_df["date"] = pd.to_datetime(book1_df["date"], errors="coerce").dt.date
    book1_df["start_time"] = book1_df.apply(lambda row: convert_time(row["start_time"], row["all_day"], is_start_time=True), axis=1)
    book1_df["end_time"] = book1_df.apply(lambda row: convert_time(row["end_time"], row["all_day"], is_start_time=False), axis=1)
    
    merged_df = pd.concat([book1_df, events_df], ignore_index=True)
    # Fix date shift before writing
    merged_df['date'] = merged_df['date'].shift(1)
    merged_df.iloc[0, merged_df.columns.get_loc('date')] = None 
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Processed data saved to {output_path}")


path_to_raw = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/raw/events_calendar/w07.txt"
path_example_columns = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/raw/events_calendar/example_columns.xlsx"

classify_and_save_w07(path_to_raw, path_example_columns, "output_01.xlsx")
