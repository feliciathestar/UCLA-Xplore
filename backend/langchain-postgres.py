from langchain_openai import ChatOpenAI 
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic.v1 import BaseModel, Field, validator
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
import re
import os
import json
from dotenv import load_dotenv

load_dotenv()

class CustomPydanticOutputParser(PydanticOutputParser):
    def get_format_instructions(self) -> str:
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

@tool
def get_date_by_reference(
    reference: str, 
    day_of_week: Optional[Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]] = None
) -> str:
    """
    Get a date based on a natural language reference and optional day of week.
    
    Args:
        reference: Natural language date reference ('today', 'tomorrow', 'next week', 'this weekend', etc.)
        day_of_week: Optional specific day of the week to find ('monday', 'tuesday', etc.)
        
    Returns:
        Date in ISO format YYYY-MM-DD
    """
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
            target_weekday = weekday_indices[day_of_week]
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
            target_weekday = weekday_indices[day_of_week]
            target_date = next_monday + timedelta(days=target_weekday)
    elif reference in ["this weekend", "upcoming weekend", "the weekend"]:
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() != 5:
            days_until_saturday = 7  
            
        if day_of_week and day_of_week in ["saturday", "sunday"]:
            if day_of_week == "saturday":
                target_date = today + timedelta(days=days_until_saturday)
            else:  
                target_date = today + timedelta(days=days_until_saturday + 1)
        else:
            target_date = today + timedelta(days=days_until_saturday)
    else:
        if day_of_week:
            current_weekday = today.weekday()
            target_weekday = weekday_indices[day_of_week]
            days_until = (target_weekday - current_weekday) % 7
            if days_until == 0:
                days_until = 7 
            target_date = today + timedelta(days=days_until)
        else:
            target_date = today
    
    return target_date.strftime("%Y-%m-%d")

@tool
def format_time_range(
    time_reference: str,
    duration_hours: Optional[float] = None
) -> Dict[str, str]:
    """
    Convert time references to standard start and end times.
    
    Args:
        time_reference: Natural language time reference ('morning', 'afternoon', 'evening', 'night', or specific time)
        duration_hours: Optional duration in hours if only start time is provided
        
    Returns:
        Dictionary with start_time and end_time in 24-hour format (HH:MM:SS)
    """
    time_reference = time_reference.lower().strip()
    
    time_ranges = {
        "morning": {"start": "06:00:00", "end": "12:00:00"},
        "afternoon": {"start": "12:00:00", "end": "17:00:00"},
        "evening": {"start": "17:00:00", "end": "21:00:00"},
        "night": {"start": "19:00:00", "end": "23:00:00"},
        "late night": {"start": "22:00:00", "end": "02:00:00"}
    }
    
    if time_reference in time_ranges:
        return time_ranges[time_reference]
    
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
            
            if duration_hours:
                end_hour = hour + int(duration_hours)
                end_minute = minute + int((duration_hours - int(duration_hours)) * 60)
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = f"{end_hour % 24:02d}:{end_minute:02d}:00"
            else:
                end_hour = (hour + 1) % 24
                end_time = f"{end_hour:02d}:{minute:02d}:00"
                
            return {"start": start_time, "end": end_time}
            
        elif re.match(r'^\d{1,2}:\d{2}$', time_reference):
            hour, minute = map(int, time_reference.split(':'))
            start_time = f"{hour:02d}:{minute:02d}:00"
            
            if duration_hours:
                end_hour = hour + int(duration_hours)
                end_minute = minute + int((duration_hours - int(duration_hours)) * 60)
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = f"{end_hour % 24:02d}:{end_minute:02d}:00"
            else:
                end_hour = (hour + 1) % 24
                end_time = f"{end_hour:02d}:{minute:02d}:00"
                
            return {"start": start_time, "end": end_time}
    except Exception:
        return {"start": "09:00:00", "end": "17:00:00"}
    
    return {"start": "09:00:00", "end": "17:00:00"}

def parse_user_query(user_query: str) -> TimeQueryData:
    """
    Parse a user's natural language query into structured data using LangChain 
    with tools
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Structured TimeQueryData object with extracted date, time, and interest information
    """
    load_dotenv()
    api_key=os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables")
    else:
        print(f"API Key found (first 10 chars): {api_key[:10]}...")
    
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=api_key
    )    
    # Setup the date and time tools
    tools = [get_date_by_reference, format_time_range]
    
    # Create a custom parser for structured output that works with pydantic v1
    parser = CustomPydanticOutputParser(pydantic_object=TimeQueryData)
    
    # Using a direct way to extract info rather than agent, since agent requires agent_scratchpad
    try:
        # First approach: Use direct query without agent
        messages = [
            {
                "role": "system", 
                "content": f"""You are an assistant that extracts structured information from user queries about UCLA events.
                Extract the following information if present:
                1. Date - Convert any date formats or references to YYYY-MM-DD 
                2. Start time and end time - Convert to 24-hour format HH:MM:SS
                3. Interests - Any extracurricular activities, clubs, or interests mentioned
                
                Today's date is {datetime.now().strftime("%Y-%m-%d")}.
                
                {parser.get_format_instructions()}"""
            },
            {"role": "user", "content": user_query}
        ]
        
        response = llm.invoke(messages)
        parsed_result = parser.parse(response.content)
        
        # Define weekday_indices here for post-processing
        weekday_indices = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Process dates and times if needed
        if parsed_result.date and parsed_result.date.lower() not in ["today", "tomorrow"]:
            # Try to convert from natural language if not already in YYYY-MM-DD format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', parsed_result.date):
                try:
                    date_parts = parsed_result.date.split()
                    if "next" in date_parts and len(date_parts) >= 2:
                        day_of_week = date_parts[1].lower() if date_parts[1].lower() in weekday_indices else None
                        parsed_result.date = get_date_by_reference("next week", day_of_week)
                    elif any(day in parsed_result.date.lower() for day in weekday_indices.keys()):
                        for day in weekday_indices.keys():
                            if day in parsed_result.date.lower():
                                parsed_result.date = get_date_by_reference("this week", day)
                                break
                except Exception as e:
                    print(f"Error processing date: {e}")
        
        # Process time descriptions if needed
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
                
        return parsed_result
                
    except Exception as e:
        print(f"Error parsing query: {e}")
        return TimeQueryData()


def test_parse_user_query():
    """Test function to demonstrate the parser with examples"""
    test_queries = [
        "I'm looking for chess club events tomorrow afternoon",
        "Are there any basketball events from 3pm to 5pm on April 15th?",
        "Show me dance workshops next Friday evening",
        "I want to join a coding club meeting this weekend",
        "Any debate team events at 2:30pm that last for 2 hours?",
        "Are there any entrepreneurship events next Tuesday morning?",
        "I'm interested in attending a photography workshop from 1pm to 3pm",
        "What volunteer opportunities are available this Thursday night?",
    ]
    
    for query in test_queries:
        result = parse_user_query(query)
        print(f"\nQuery: {query}")
        print(f"Date: {result.date}")
        print(f"Start time: {result.start_time}")
        print(f"End time: {result.end_time}")
        print(f"Interests: {result.interests}")

if __name__ == "__main__":
    test_parse_user_query()