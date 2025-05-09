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
            "date": {
                "title": "Date",
                "description": "Date in ISO format YYYY-MM-DD, e.g. 2025-04-15",
                "type": "string",
                "format": "date"
            },
            "start_time": {
                "title": "Start Time",
                "description": "Start time in 24-hour format (HH:MM:SS), e.g. 14:30:00",
                "type": "string",
                "format": "time"
            },
            "end_time": {
                "title": "End Time", 
                "description": "End time in 24-hour format (HH:MM:SS), e.g. 16:00:00",
                "type": "string",
                "format": "time"
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
    
    return f"The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\n{schema_str}\n\nAs an example, for the schema {{'properties': {{'foo': {{'title': 'Foo', 'description': 'a list of strings', 'type': 'array', 'items': {{'type': 'string'}}}}}}, 'required': ['foo']}}, the object {{'foo': ['bar', 'baz']}} is a well-formatted instance."

class TimeQueryData(BaseModel):
    """Data structure for parsed time-related queries"""
    date: Optional[str] = Field(None, description="Date in ISO format YYYY-MM-DD, e.g. 2025-04-15")
    start_time: Optional[str] = Field(None, description="Start time in 24-hour format (HH:MM:SS), e.g. 14:30:00")
    end_time: Optional[str] = Field(None, description="End time in 24-hour format (HH:MM:SS), e.g. 16:00:00")
    interests: List[str] = Field([], description="List of extracurricular interests mentioned")
    
    @validator('date')
    def validate_date(cls, v):
        if v is None:
            return None
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
    
    @validator('start_time', 'end_time')
    def validate_time(cls, v):
        if v is None:
            return None
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', v):
            raise ValueError("Invalid time format. Expected HH:MM:SS in 24-hour format")
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
    elif reference in ["this week", "current week"]:
        if not day_of_week:
            target_date = today
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
            
        if day_of_week and day_of_week.lower() in ["saturday", "sunday"]:
            if day_of_week.lower() == "saturday":
                target_date = today + timedelta(days=days_until_saturday)
            else:
                target_date = today + timedelta(days=days_until_saturday + 1)
        else:
            target_date = today + timedelta(days=days_until_saturday)
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
        # Create the prompt for the model
        system_content = f"""You are an assistant that extracts structured information from user queries about UCLA events.
        Extract the following information if present:
        1. Date - Convert any date formats or references to YYYY-MM-DD 
        2. Start time and end time - Convert to 24-hour format HH:MM:SS
        3. Interests - Any extracurricular activities, clubs, or interests mentioned
        
        Today's date is {datetime.now().strftime("%Y-%m-%d")}.
        
        {get_format_instructions()}
        IMPORTANT TIME GUIDELINES:
        - For "morning" or "in the morning", use 06:00:00 to 12:00:00
        - For "afternoon", use 12:00:00 to 17:00:00
        - For "evening" or "early evening", use 17:00:00 to 21:00:00
        - For "night" or "night hours", use 19:00:00 to 23:00:00
        - For "late night", use 22:00:00 to 02:00:00
        - For "lunchtime", use approximately 12:00:00 to 13:00:00

        Infer any missing information based on the context of the query.
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
            # Look for JSON-like content within the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', content)
            if json_match:
                json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
                json_data = json.loads(json_str)
            else:
                json_data = json.loads(content)
                
            # Create TimeQueryData object
            parsed_result = TimeQueryData(
                date=json_data.get('date'),
                start_time=json_data.get('start_time'),
                end_time=json_data.get('end_time'),
                interests=json_data.get('interests', [])
            )
            
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            # Fallback to creating an empty object
            parsed_result = TimeQueryData()
        
        # Post-process dates and times for consistency
        weekday_indices = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Process dates if needed
        if parsed_result.date and not re.match(r'^\d{4}-\d{2}-\d{2}$', parsed_result.date):
            try:
                # Handle cases like "next Monday", "this weekend", etc.
                if "next" in parsed_result.date.lower():
                    for day in weekday_indices:
                        if day in parsed_result.date.lower():
                            parsed_result.date = get_date_by_reference("next week", day)
                            break
                elif "this" in parsed_result.date.lower():
                    for day in weekday_indices:
                        if day in parsed_result.date.lower():
                            parsed_result.date = get_date_by_reference("this week", day)
                            break
                elif "tomorrow" in parsed_result.date.lower():
                    parsed_result.date = get_date_by_reference("tomorrow")
                elif "weekend" in parsed_result.date.lower():
                    parsed_result.date = get_date_by_reference("this weekend")
                elif any(day in parsed_result.date.lower() for day in weekday_indices):
                    for day in weekday_indices:
                        if day in parsed_result.date.lower():
                            parsed_result.date = get_date_by_reference("this week", day)
                            break
            except Exception as e:
                print(f"Error processing date: {e}")
        
        if parsed_result.start_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', parsed_result.start_time):
            try:
                time_info = format_time_range(parsed_result.start_time)
                parsed_result.start_time = time_info["start"]
                if not parsed_result.end_time:
                    parsed_result.end_time = time_info["end"]
            except Exception as e:
                print(f"Error processing start time: {e}")
                
        if parsed_result.end_time and not re.match(r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$', parsed_result.end_time):
            try:
                time_info = format_time_range(parsed_result.end_time)
                parsed_result.end_time = time_info["end"]
            except Exception as e:
                print(f"Error processing end time: {e}")

        if parsed_result.start_time and not parsed_result.end_time:
            # Convert start time to datetime object
            start_time_parts = list(map(int, parsed_result.start_time.split(':')))
            start_dt = datetime.now().replace(
                hour=start_time_parts[0], 
                minute=start_time_parts[1], 
                second=start_time_parts[2]
            )
            # Add 2 hours for default duration
            end_dt = start_dt + timedelta(hours=2)
            parsed_result.end_time = end_dt.strftime("%H:%M:%S")
        
        return parsed_result
            
    except Exception as e:
        print(f"Error parsing query: {e}")
        return TimeQueryData()

def extract_query_parameters(user_query: str) -> Dict[str, Any]:
    """
    Process a user query and extract structured parameters for database queries.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Dictionary with extracted parameters (date, start_time, end_time, interests)
    """
    parsed_data = parse_user_query(user_query)
    

    result = {
        "date": parsed_data.date or datetime.now().strftime("%Y-%m-%d"), 
        "start_time": parsed_data.start_time or "00:00:00",  
        "end_time": parsed_data.end_time or "23:59:59",  
        "interests": parsed_data.interests or []
    }
    
    print(f"Extracted query parameters: {result}")
    return result

# Test function for interactive testing
def test_parse_user_query():
    """Interactive test function for query parsing"""
    test_queries = [

        ### test 1
        # "I'm looking for chess club events tomorrow afternoon",
        # "Are there any basketball events from 3pm to 5pm on April 15th?",
        # "Show me dance workshops next Friday evening",
        # "I want to join a coding club meeting this weekend",
        # "Any debate team events at 2:30pm that last for 2 hours?",
        # "Are there any entrepreneurship events next Tuesday morning?",
        # "I'm interested in attending a photography workshop from 1pm to 3pm",
        # "What volunteer opportunities are available this Thursday night?",

        "Let me know if anything fitness-related is happening around lunchtime this Sunday.",
        "Do you have listings for art exhibits that begin between 10:45 and 12:15 next week?",
        "Find me something music-related on the first Friday of next month, ideally in the early evening.",
        "Looking to volunteer sometime after 4:30 PM on Tuesday – anything open then?",
        "Is there anything going on related to mental health awareness during the night hours this weekend?",
        "Check for anything involving robotics club activity tomorrow between 14:00 and 16:00.",
        "Tell me if there’s a public speaking workshop anytime next Wednesday.",
        "I’d like to know about any e-sports meetups happening late at night on Saturday.",
        "Show me community outreach events on the 20th from 8 in the morning.",
        "Are there networking events that go until 9pm next Thursday?"

    ]
    
    for query in test_queries:
        result = parse_user_query(query)
        print(f"\nQuery: {query}")
        print(f"Date: {result.date}")
        print(f"Start time: {result.start_time}")
        print(f"End time: {result.end_time}")
        print(f"Interests: {result.interests}")
        print("-" * 50)

if __name__ == "__main__":
    test_parse_user_query()