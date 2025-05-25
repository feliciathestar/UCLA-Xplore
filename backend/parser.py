from pydantic.v1 import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
import re
import os
import json
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Replace the LangChain custom parser with our own JSON schema helper
def get_format_instructions() -> str:
    schema = {
        "properties": {
            "dates": {
                "title": "Dates",
                "description": "List of dates in ISO format YYYY-MM-DD",
                "type": "array",
                "items": {"type": "string", "format": "date"}
            },
            "time_slots": {
                "title": "Time Slots",
                "description": "List of time ranges with start_time and end_time in 24-hour format",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "format": "time"},
                        "end_time": {"type": "string", "format": "time"}
                    },
                    "required": ["start_time", "end_time"]
                }
            },
            "interests": {
                "title": "Interests",
                "description": "List of extracurricular interests mentioned",
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "type": "object"
    }
    
    schema_str = json.dumps(schema)
    return f"The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\n{schema_str}"

class TimeQueryData(BaseModel):
    """Data structure for parsed time-related queries"""
    dates: List[str] = Field([], description="List of dates in ISO format YYYY-MM-DD")
    time_slots: List[Dict[str, str]] = Field([], description="List of time slots with start_time and end_time")
    interests: List[str] = Field([], description="List of extracurricular interests mentioned")
    
    # Keep backward compatibility
    date: Optional[str] = Field(None, description="Single date for backward compatibility")
    start_time: Optional[str] = Field(None, description="Single start time for backward compatibility")
    end_time: Optional[str] = Field(None, description="Single end time for backward compatibility")
    
    @validator('dates')
    def validate_dates(cls, v):
        for date in v:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
        return v
    
    @validator('time_slots')
    def validate_time_slots(cls, v):
        for slot in v:
            start_time = slot.get("start_time")
            end_time = slot.get("end_time")
            if start_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', start_time):
                raise ValueError(f"Invalid start_time format: {start_time}")
            if end_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', end_time):
                raise ValueError(f"Invalid end_time format: {end_time}")
        return v

# Define utility functions for date/time processing
def get_date_by_reference(reference: str, day_of_week: Optional[str] = None) -> str:
    """Process natural language date references into ISO format dates"""
    today = datetime.now()
    reference = reference.lower().strip()
    
    weekday_indices = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    if reference == "today":
        target_date = today
    elif reference == "tomorrow":
        target_date = today + timedelta(days=1)
    elif reference in ["weekdays", "weekday"]:
        # Return all weekdays (Monday-Friday) from current week
        current_weekday = today.weekday()
        dates = []
        for i in range(5):  # Monday to Friday
            days_until = (i - current_weekday) % 7
            if days_until == 0 and current_weekday == i:
                dates.append(today.strftime("%Y-%m-%d"))
            else:
                dates.append((today + timedelta(days=days_until)).strftime("%Y-%m-%d"))
        return dates  # Return list for weekdays
    elif reference in ["this week", "current week"]:
        if not day_of_week:
            # Return all days of this week
            current_weekday = today.weekday()
            dates = []
            for i in range(7):
                days_until = (i - current_weekday) % 7
                dates.append((today + timedelta(days=days_until)).strftime("%Y-%m-%d"))
            return dates
        else:
            current_weekday = today.weekday()
            target_weekday = weekday_indices.get(day_of_week.lower(), 0)
            days_until = (target_weekday - current_weekday) % 7
            if days_until == 0 and current_weekday == target_weekday:
                target_date = today
            else:
                target_date = today + timedelta(days=days_until)
    elif reference in ["next week"]:
        days_until_monday = (0 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        if not day_of_week:
            target_date = next_monday
        else:
            target_weekday = weekday_indices.get(day_of_week.lower(), 0)
            target_date = next_monday + timedelta(days=target_weekday)
    elif reference in ["this weekend", "upcoming weekend", "the weekend"]:
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() != 5:
            days_until_saturday = 7
            
        # Return both Saturday and Sunday
        saturday = today + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        return [saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")]
    else:
        if day_of_week:
            current_weekday = today.weekday()
            target_weekday = weekday_indices.get(day_of_week.lower(), 0)
            days_until = (target_weekday - current_weekday) % 7
            if days_until == 0:
                days_until = 7
            target_date = today + timedelta(days=days_until)
        else:
            target_date = today
    
    return target_date.strftime("%Y-%m-%d")

def format_time_range(time_reference: str) -> Dict[str, str]:
    """Convert natural language time references to structured time ranges"""
    time_reference = time_reference.lower().strip()
    
    time_ranges = {
        "morning": {"start": "06:00:00", "end": "12:00:00"},
        "afternoon": {"start": "12:00:00", "end": "17:00:00"},
        "evening": {"start": "17:00:00", "end": "21:00:00"},
        "night": {"start": "19:00:00", "end": "23:00:00"},
        "late night": {"start": "22:00:00", "end": "02:00:00"}
    }
    
    # Step 1: Direct matching for efficiency
    if time_reference in time_ranges:
        return time_ranges[time_reference]
    
    # Step 2: Try regex patterns for common time formats
    try:
        if re.match(r'^\d{1,2}(:\d{2})?(am|pm)$', time_reference):
            parts = re.match(r'^(\d{1,2})(?::(\d{2}))?(am|pm)$', time_reference)
            hour = int(parts.group(1))
            minute = int(parts.group(2) or 0)
            ampm = parts.group(3)
            
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
                
            start_time = f"{hour:02d}:{minute:02d}:00"
            end_hour = (hour + 2) % 24  
            end_time = f"{end_hour:02d}:{minute:02d}:00"
            
            return {"start": start_time, "end": end_time}
            
        elif re.match(r'^\d{1,2}:\d{2}$', time_reference):
            hour, minute = map(int, time_reference.split(':'))
            start_time = f"{hour:02d}:{minute:02d}:00"
            end_hour = (hour + 2) % 24  
            end_time = f"{end_hour:02d}:{minute:02d}:00"
            
            return {"start": start_time, "end": end_time}
    except Exception as e:
        print(f"Regex time parsing error: {e}")
    
    # Step 3: LLM fallback for more complex expressions
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found for time parsing")
            return {"start": "09:00:00", "end": "17:00:00"}
            
        client = openai.OpenAI(api_key=api_key)
        
        # Create a specific prompt for time interpretation
        time_prompt = f"""
        Convert this time reference into a start and end time in 24-hour format (HH:MM:SS): "{time_reference}"
        
        Use these standard time ranges as reference:
        - morning: 06:00:00 to 12:00:00
        - afternoon: 12:00:00 to 17:00:00
        - evening: 17:00:00 to 21:00:00
        - night: 19:00:00 to 23:00:00
        - late night: 22:00:00 to 02:00:00
        
        Output ONLY a JSON object with "start" and "end" keys, nothing else.
        For example: {{"start": "19:00:00", "end": "21:00:00"}}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": time_prompt}]
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from the content
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', content)
        if json_match:
            json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
            json_data = json.loads(json_str)
        else:
            json_data = json.loads(content)
        
        # Validate the format of start and end times
        start_time = json_data.get("start")
        end_time = json_data.get("end")
        
        if start_time and end_time:
            if re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', start_time) and \
               re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', end_time):
                return {"start": start_time, "end": end_time}
        
        # If LLM returns invalid format, check for partial matches in time_ranges
        for key, value in time_ranges.items():
            if key in time_reference:
                return value
                
        return {"start": "09:00:00", "end": "17:00:00"}
        
    except Exception as e:
        print(f"LLM time parsing error: {e}")
        return {"start": "09:00:00", "end": "17:00:00"}

def parse_user_query(user_query: str) -> TimeQueryData:
    """
    Parse a user query into structured time and interest data.
    Uses OpenAI directly to match the FastAPI architecture.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Structured TimeQueryData object with extracted date, time, and interest information
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables")
        return TimeQueryData()
        
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Enhanced prompt to handle complex date-time combinations
        system_content = f"""You are an assistant that extracts structured information from user queries about UCLA events.
        Extract the following information if present:
        1. Dates - Convert any date formats or references to YYYY-MM-DD format. Support multiple dates.
        2. Time slots - Extract unique time ranges with start_time and end_time in 24-hour format HH:MM:SS
        3. Interests - Any extracurricular activities, clubs, or interests mentioned
        
        Today's date is {datetime.now().strftime("%Y-%m-%d")}.
        
        IMPORTANT RULES:
        - Create SEPARATE arrays for dates and time_slots
        - Do NOT duplicate time slots for each date
        - For "Monday and Tuesday from 3-5pm", create: dates=["2025-05-26", "2025-05-27"], time_slots=[{{"start_time": "15:00:00", "end_time": "17:00:00"}}]
        - For "weekdays 2-4pm or 6-8pm", create: dates=[all weekdays], time_slots=[{{"start_time": "14:00:00", "end_time": "16:00:00"}}, {{"start_time": "18:00:00", "end_time": "20:00:00"}}]
        - Only create multiple time slots when there are genuinely different time ranges mentioned
        
        Examples:
        - "Events on Monday and Tuesday from 2-4pm" → dates: ["Mon", "Tue"], time_slots: [{"2pm-4pm"}]
        - "Monday 9am and Tuesday 2pm" → dates: ["Mon", "Tue"], time_slots: [{"9am-11am"}, {"2pm-4pm"}]
        - "Weekdays morning and evening" → dates: [Mon-Fri], time_slots: [{"morning"}, {"evening"}]
        
        {get_format_instructions()}
        
        CRITICAL: Do not repeat the same time slot multiple times. Each unique time range should appear only once in the time_slots array.
        """
        
        # Make the API call using the OpenAI client
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_query}
            ]
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Parse the response JSON into our data model
        try:
            # First try to extract JSON from the text
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', content)
            if json_match:
                json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
                json_data = json.loads(json_str)
            else:
                json_data = json.loads(content)
                
            # Create TimeQueryData object
            parsed_result = TimeQueryData(
                dates=json_data.get('dates', []),
                time_slots=json_data.get('time_slots', []),
                interests=json_data.get('interests', [])
            )
            
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            parsed_result = TimeQueryData()
        
        # Enhanced post-processing for edge cases
        weekday_indices = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Process dates with special handling for weekdays and weekends
        if parsed_result.dates:
            processed_dates = []
            for date in parsed_result.dates:
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                    try:
                        # Handle weekdays expansion
                        if "weekday" in date.lower():
                            weekday_dates = get_date_by_reference("weekdays")
                            if isinstance(weekday_dates, list):
                                processed_dates.extend(weekday_dates)
                            else:
                                processed_dates.append(weekday_dates)
                            continue
                        
                        # Handle weekend expansion  
                        elif "weekend" in date.lower():
                            weekend_dates = get_date_by_reference("this weekend")
                            if isinstance(weekend_dates, list):
                                processed_dates.extend(weekend_dates)
                            else:
                                processed_dates.append(weekend_dates)
                            continue
                        
                        # Handle "this week" expansion
                        elif "this week" in date.lower() and "this week" == date.lower().strip():
                            week_dates = get_date_by_reference("this week")
                            if isinstance(week_dates, list):
                                processed_dates.extend(week_dates)
                            else:
                                processed_dates.append(week_dates)
                            continue
                            
                        # Handle other date references
                        elif "next" in date.lower():
                            for day in weekday_indices:
                                if day in date.lower():
                                    processed_date = get_date_by_reference("next week", day)
                                    processed_dates.append(processed_date)
                                    break
                        elif "this" in date.lower():
                            for day in weekday_indices:
                                if day in date.lower():
                                    processed_date = get_date_by_reference("this week", day)
                                    processed_dates.append(processed_date)
                                    break
                        elif "tomorrow" in date.lower():
                            processed_date = get_date_by_reference("tomorrow")
                            processed_dates.append(processed_date)
                        elif any(day in date.lower() for day in weekday_indices):
                            for day in weekday_indices:
                                if day in date.lower():
                                    processed_date = get_date_by_reference("this week", day)
                                    processed_dates.append(processed_date)
                                    break
                    except Exception as e:
                        print(f"Error processing date: {e}")
                else:
                    processed_dates.append(date)
            
            parsed_result.dates = processed_dates
        
        # Enhanced time slot processing with duration fixing
        if parsed_result.time_slots:
            processed_time_slots = []
            for slot in parsed_result.time_slots:
                start_time = slot.get("start_time")
                end_time = slot.get("end_time")
                
                # Fix time format if needed
                if start_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', start_time):
                    try:
                        time_info = format_time_range(start_time)
                        start_time = time_info["start"]
                        if not end_time:
                            end_time = time_info["end"]
                    except Exception as e:
                        print(f"Error processing start time: {e}")
                        continue
                
                if end_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', end_time):
                    try:
                        time_info = format_time_range(end_time)
                        end_time = time_info["end"]
                    except Exception as e:
                        print(f"Error processing end time: {e}")
                        continue
                
                # Fix same start/end time issue
                if start_time == end_time:
                    try:
                        start_parts = list(map(int, start_time.split(':')))
                        start_dt = datetime.now().replace(
                            hour=start_parts[0], 
                            minute=start_parts[1], 
                            second=start_parts[2]
                        )
                        # Add 2 hours for default duration
                        end_dt = start_dt + timedelta(hours=2)
                        end_time = end_dt.strftime("%H:%M:%S")
                    except Exception as e:
                        print(f"Error fixing time duration: {e}")
                        end_time = "23:59:59"  # Fallback
                
                processed_time_slots.append({
                    "start_time": start_time,
                    "end_time": end_time
                })
            
            parsed_result.time_slots = processed_time_slots
        
        return parsed_result
            
    except Exception as e:
        print(f"Error parsing query: {e}")
        return TimeQueryData()

def extract_query_parameters(user_query: str) -> Dict[str, Any]:
    """
    Process a user query and extract structured parameters for database queries.
    Supports both single and multiple dates/time slots with deduplication.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Dictionary with extracted parameters (dates, time_slots, interests)
    """
    parsed_data = parse_user_query(user_query)
    
    # Handle multiple dates and time slots
    dates = parsed_data.dates if parsed_data.dates else []
    time_slots = parsed_data.time_slots if parsed_data.time_slots else []
    
    # Backward compatibility: convert single date/time to list format
    if not dates and parsed_data.date:
        dates = [parsed_data.date]
    
    if not time_slots and parsed_data.start_time and parsed_data.end_time:
        time_slots = [{"start_time": parsed_data.start_time, "end_time": parsed_data.end_time}]
    
    # DEDUPLICATION LOGIC - Remove duplicate time slots
    unique_time_slots = []
    seen_time_slots = set()
    
    for slot in time_slots:
        # Create a hashable key for the time slot
        slot_key = (slot.get("start_time"), slot.get("end_time"))
        if slot_key not in seen_time_slots:
            seen_time_slots.add(slot_key)
            unique_time_slots.append(slot)
    
    # Remove duplicate dates as well
    unique_dates = list(dict.fromkeys(dates))  # Preserves order while removing duplicates
    
    # Default fallbacks
    if not unique_dates:
        unique_dates = [datetime.now().strftime("%Y-%m-%d")]
    
    if not unique_time_slots:
        unique_time_slots = [{"start_time": "00:00:00", "end_time": "23:59:59"}]
    
    result = {
        "dates": unique_dates,
        "time_slots": unique_time_slots,
        "interests": parsed_data.interests or [],
        # Keep old format for backward compatibility
        "date": unique_dates[0] if unique_dates else None,
        "start_time": unique_time_slots[0]["start_time"] if unique_time_slots else None,
        "end_time": unique_time_slots[0]["end_time"] if unique_time_slots else None
    }
    
    print(f"Before deduplication: {len(dates)} dates, {len(time_slots)} time slots")
    print(f"After deduplication: {len(unique_dates)} dates, {len(unique_time_slots)} time slots")
    print(f"Total combinations: {len(unique_dates)} × {len(unique_time_slots)} = {len(unique_dates) * len(unique_time_slots)}")
    print(f"Extracted query parameters: {result}")
    return result

# Test function for interactive testing
def test_parse_user_query():
    """Interactive test function for query parsing with focus on multiple dates and time slots"""
    test_queries = [
        # Single date, multiple time slots
        "Events on Monday from 9am-12pm and 2pm-5pm",
        "Show me workshops tomorrow morning and evening",
        "Any meetings on Friday between 10-12 and 3-5?",
        
        # Multiple dates, single time slot
        "Basketball events on Monday and Tuesday from 3pm to 5pm",
        "Dance workshops on Wednesday and Friday evening",
        "Coding club meetings this Monday, Wednesday, and Friday at 2pm",
        
        # Multiple dates, multiple time slots
        "Events on Monday and Tuesday from 9am-12pm and 2pm-5pm",
        "Show me workshops this week in the morning and evening",
        "Any meetings on the 25th, 26th, and 27th between 9am-12pm or 2pm-5pm",
        "Find events on Wednesday and Thursday from 10-11am, 1-3pm, and 6-8pm",
        
        # Complex natural language with multiple time references
        "Chess club events tomorrow afternoon and next Monday morning",
        "Art exhibits that start between 10:45 and 12:15 on Tuesday and Thursday",
        "Volunteer opportunities after 4:30 PM on Monday, Wednesday, and Friday",
        "Fitness activities during lunchtime and evening hours this weekend",
        
        # Edge cases
        "Events on Monday from morning to afternoon",  # Should create multiple slots
        "Robotics club tomorrow between 14:00 and 16:00, and Saturday night",
        "Networking events that go until 9pm on Tuesday and Thursday",
        "Public speaking workshops anytime next Wednesday and Friday",
        
        # Real-world complex queries
        "I'm looking for music events on Monday evening, Wednesday afternoon, and Friday morning",
        "Show me tech meetups this week during lunch hours and after work",
        "Any entrepreneurship events on weekdays between 2-4pm or 6-8pm?",
    ]
    
    print("=== TESTING MULTI-TIMESLOT DETECTION ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"TEST {i}: {query}")
        print("-" * 60)
        
        try:
            # Test the parsing
            result = parse_user_query(query)
            
            # Test the parameter extraction
            params = extract_query_parameters(query)
            
            print(f"📅 Dates: {result.dates}")
            print(f"⏰ Time Slots: {result.time_slots}")
            print(f"🎯 Interests: {result.interests}")
            
            print(f"\n📊 Final Parameters:")
            print(f"   dates: {params['dates']}")
            print(f"   time_slots: {params['time_slots']}")
            print(f"   interests: {params['interests']}")
            
            # Analyze the results
            num_dates = len(params['dates'])
            num_time_slots = len(params['time_slots'])
            
            if num_dates > 1 and num_time_slots > 1:
                print(f"✅ MULTI-DETECTION: {num_dates} dates × {num_time_slots} time slots = {num_dates * num_time_slots} combinations")
            elif num_dates > 1:
                print(f"📅 MULTI-DATE: {num_dates} dates detected")
            elif num_time_slots > 1:
                print(f"⏰ MULTI-TIMESLOT: {num_time_slots} time slots detected")
            else:
                print(f"📍 SINGLE: 1 date, 1 time slot")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("=" * 80)
        print()

def test_specific_multi_timeslot_cases():
    """Test specific edge cases for multi-timeslot detection"""
    print("\n=== SPECIFIC MULTI-TIMESLOT EDGE CASES ===\n")
    
    edge_cases = [
        "Events Monday and Tuesday 9-11am, 1-3pm, 5-7pm",  # 2 dates × 3 time slots
        "Workshops this week morning, afternoon, evening",  # 1 date × 3 time slots
        "Monday 9am, Tuesday 2pm, Wednesday 6pm",  # 3 dates × implicit 1 time slot each
        "Tomorrow from 10-12, 2-4, and 6-8",  # 1 date × 3 time slots
        "Weekdays between 9-10am or 3-4pm",  # Multiple dates × 2 time slots
    ]
    
    for case in edge_cases:
        print(f"EDGE CASE: {case}")
        params = extract_query_parameters(case)
        dates = params['dates']
        time_slots = params['time_slots']
        combinations = len(dates) * len(time_slots)
        
        print(f"Result: {len(dates)} dates × {len(time_slots)} time slots = {combinations} combinations")
        print(f"Dates: {dates}")
        print(f"Time slots: {time_slots}")
        print("-" * 50)
        print()

if __name__ == "__main__":
    test_parse_user_query()
    test_specific_multi_timeslot_cases()