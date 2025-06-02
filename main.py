# FastAPI 
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# authentication and authorization
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# database connection
import psycopg2
import os
from dotenv import load_dotenv
from pymilvus import connections, Collection
import openai

# UI imports
from fastapi.responses import StreamingResponse

# Other imports
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

# Internal imports
from backend.parser import extract_query_parameters


# Initialize FastAPI app
app = FastAPI()
load_dotenv()

# Milvus connection constants
MILVUS_ENDPOINT = os.getenv("MILVUS_ENDPOINT")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME")

# OpenAI constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any domain
    allow_credentials=True,  # Allows cookies in cross-origin requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# JWT configuration
SECRET_KEY = "your_secret_key"  # change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# In-memory "database" for demo purposes
fake_users_db = {}

#####################################
### Define data validation models ###
#####################################
# converting an object into a format like JSON or XML that can be stored or transmitted over a network.
class User(BaseModel):
    # Internal user representation with secure password storage
    username: str
    email: str
    hashed_password: str

class UserIn(BaseModel):
    # User registration model with raw password
    username: str
    email: str
    password: str

class Token(BaseModel):
    # Authentication token response
    access_token: str
    token_type: str

class TimeSlotModel(BaseModel):
    date: str
    start_time: str
    end_time: str

class ChatRequest(BaseModel):
    # Incoming chat message from user
    message: str
    timeSlots: Optional[List[TimeSlotModel]] = None

class ChatResponse(BaseModel):
    # Outgoing response to user
    response: str

#########################
### Utility functions ###
#########################
def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash a password for data security.
    """
    return pwd_context.hash(password)

def create_jwt(data: dict, expires_delta: Optional [timedelta] = None) -> str:
    """
    Creates a JWT token with expiration.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    # Use global constant for default expiration
    expiration = expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expiration
    to_encode.update({"exp": expire})
    
    try:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        # Log the error in a production environment
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create authentication token"
        )

def get_user(username: str):
    """
    Get a user from the in-memory database
    args:
        username: The username from user input
    returns:
        User object if found, None otherwise
    """
    user = fake_users_db.get(username)
    if user:
        return User(**user)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """"
    Get the current user from the JWT token.
    Args:
        token: JWT token string
    Returns:
        User object if the token is valid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user


##################
### API routes ###
##################

@app.get("/")
async def root():
    return {"message": "Welcome to the UCLA-Xplore API!"}

##########################
### Postgres Functions ###
##########################

def query_postgres(params: Dict[str, Any] = None, direct_time_slots: list = None):
    """
    Query PostgreSQL database based on extracted parameters or direct time slots.
    Supports multiple dates and time slots from both natural language parsing and UI selection.
    
    Args:
        params: Dictionary of parsed parameters from natural language (optional)
        direct_time_slots: List of time slot objects directly from UI (optional)
    """
    try:
        dates = []
        time_slots = []
        
        # Handle direct time slots from graphical UI time slot selector
        if direct_time_slots:
            # Process the time slots data from your UI component
            # You'll need to format this based on how your timetable component sends data
            for slot in direct_time_slots:
                # Assuming each slot has date, start_time, end_time
                if slot.get("date") not in dates:
                    dates.append(slot["date"])
                time_slots.append({
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"]
                })
        
        # Handle parsed parameters from natural language
        elif params:
            dates = params.get("dates", [params.get("date")]) if params.get("date") else params.get("dates", [])
            time_slots = params.get("time_slots", [])
            
            # If using old format with single date and times
            if params.get("date") and params.get("start_time") and params.get("end_time"):
                dates = [params["date"]]
                time_slots = [{"start_time": params["start_time"], "end_time": params["end_time"]}]

        # Validate inputs
        if not dates or not time_slots:
            print("No dates or time slots provided")
            return []

        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            sslmode=os.getenv('DB_SSLMODE')  
        )

        cur = conn.cursor()
        
        # Build dynamic query for multiple dates and time slots
        conditions = []
        query_params = []
        
        for date in dates:
            for time_slot in time_slots:
                start_time = time_slot.get("start_time")
                end_time = time_slot.get("end_time")
                
                if start_time and end_time:
                    conditions.append("(date = %s AND start_time >= %s AND end_time <= %s)")
                    query_params.extend([date, start_time, end_time])
        
        if not conditions:
            print("No valid date/time combinations found")
            cur.close()
            conn.close()
            return []
        
        # Combine all conditions with OR
        query = f"""
        SELECT DISTINCT event_id FROM events 
        WHERE {' OR '.join(conditions)}
        """
        
        cur.execute(query, query_params)
        matching_events = cur.fetchall()

        # Format results as list of event IDs
        event_ids = [str(event[0]) for event in matching_events]

        cur.close()
        conn.close()

        return event_ids

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Error processing query: {e}")
        return []


########################
### Milvus functions ###
########################

def initialize_milvus():
    connections.connect(uri=MILVUS_ENDPOINT, token=MILVUS_TOKEN)
    collection = Collection(MILVUS_COLLECTION_NAME)
    collection.load()
    return collection

def query_milvus_by_single_id(event_id):
    """
    Query Milvus database by one exact event ID
    
    Args:
        event_id: The ID of the event to retrieve
        
    Returns:
        Dictionary with event details or error message
    """
    try:
        collection = initialize_milvus()
        expr = f"event_id == {event_id}"
        results = collection.query(
            expr,
            output_fields=["event_name", "event_tags", "event_programe", "event_location", "event_description"]
        )
        return results
    except Exception as e:
        return f"Milvus query error: {e}"

def query_milvus_by_list_id(event_ids: list):
    """
    Query Milvus database by multiple event IDs as a list
    
    Args:
        event_ids: List of event IDs to retrieve
        
    Returns:
        Dictionary with event details or error message
    """
    try:
        collection = initialize_milvus()
        
        # Convert list to comma-separated string for Milvus query
        ids_str = ",".join(str(id) for id in event_ids)
        expr = f"event_id in [{ids_str}]"
        
        results = collection.query(
            expr,
            output_fields=["event_name", "event_tags", "event_programe", "event_location", "event_description"]
        )
        return results
    except Exception as e:
        return f"Milvus query error: {e}"

def query_milvus_by_vector_similarity(query_text, top_k=5):
    """
    Query Milvus database using semantic similarity search
    Used for when there is no event ID to search for (e.g., no time contraints)
    
    Args:
        query_text: The text to search for
        top_k: Number of top results to return
        
    Returns:
        List of semantically similar events
    """
    try:
        collection = initialize_milvus()
        query_embedding = get_openai_embedding(query_text)
        
        if not query_embedding:
            return "Failed to generate embedding for search"
        
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["event_id", "event_name", "event_tags", "event_programe", "event_location", "event_description"]
        )

        # Format the results
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.entity.get("event_id"),
                    "name": hit.entity.get("event_name"),
                    "tags": hit.entity.get("event_tags"),
                    "program": hit.entity.get("event_programe"),
                    "location": hit.entity.get("event_location"),
                    "description": hit.entity.get("event_description"),
                    "similarity": hit.distance
                })
        
        return formatted_results
    except Exception as e:
        return f"Milvus search error: {e}"

def generate_llm_response(milvus_result):
    """
    Generate a natural language response about events using OpenAI's API.
    
    Args:
        milvus_result: List of event details from Milvus query or error string
        
    Returns:
        String containing a natural language response about relevant events
    """
    try:
        # Handle error strings from Milvus
        if isinstance(milvus_result, str):
            print(f"Error from Milvus: {milvus_result}")
            return f"Sorry, I encountered an issue while retrieving event information: {milvus_result}"
        
        # Handle empty results
        if not milvus_result:
            return "I couldn't find any events matching your criteria. Perhaps try a different date, time, or interests?"
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Format event information for the prompt
        events_text = ""
        for event in milvus_result:
            # Fix: Use the correct field names from your Milvus results
            events_text += f"\nEvent: {event.get('name', 'Unnamed event')}\n"
            events_text += f"Location: {event.get('location', 'Location TBD')}\n"
            events_text += f"Program: {event.get('program', 'N/A')}\n"
            
            # Handle tags properly - could be a string or a list
            tags = event.get('tags', [])
            if isinstance(tags, list):
                events_text += f"Tags: {', '.join(tags) if tags else 'N/A'}\n"
            else:
                events_text += f"Tags: {tags if tags else 'N/A'}\n"
            
            events_text += f"Description: {event.get('description', 'No description available')}\n"
        
        # Debug: Print the formatted events text
        print(f"DEBUG: Formatted events text for LLM:\n{events_text}")
        
        # Create the prompt for GPT
        prompt = f"""Based on the following UCLA events, provide a concise and natural response highlighting the most relevant details. 
        Focus on key information like event names, times, locations, and any special features. Keep the response friendly and informative.
        
        Events:{events_text}
        
        Response:"""
        
        print(f"DEBUG: Full prompt being sent to OpenAI:\n{prompt}")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides information about UCLA events."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        # Extract and return the generated response
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Sorry, I couldn't process the events information at this time. Error: {str(e)}"

def get_openai_embedding(text: str):
    """
    Generate OpenAI embedding for the given text.
    
    Args:
        text: The text to generate embedding for
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating OpenAI embedding: {e}")
        return None


# Chat endpoint – temporarily bypasses authentication
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    try:
        # Pipeline: Parse -> Postgres (time filter) -> Milvus (Interest filter) -> LLM
        print("\n=== Starting Chat Pipeline ===")
        print(f"📨 Received message: {chat_request.message}")
        print(f"🕐 Received time slots: {chat_request.timeSlots}")
        
        # Convert Pydantic models to dictionaries for the query function
        time_slots_dict = None
        if chat_request.timeSlots:
            time_slots_dict = [slot.dict() for slot in chat_request.timeSlots]
            print(f"🔄 Converted time slots: {time_slots_dict}")
        
        print("\n1. Processing query parameters...")
        # Use direct time slots if provided, otherwise parse the message
        if time_slots_dict and len(time_slots_dict) > 0:
            print("🎯 Using direct time slots from UI")
            print(f"Time slots data: {time_slots_dict}")
        else:
            print("📝 Parsing message for query parameters")
            query_params = extract_query_parameters(chat_request.message)
            print(f"Extracted parameters: {query_params}")
        
        print("\n2. Querying Postgres for date/time filtering...")
        if time_slots_dict and len(time_slots_dict) > 0:
            event_ids = query_postgres(direct_time_slots=time_slots_dict)
        else:
            event_ids = query_postgres(params=query_params if 'query_params' in locals() else None)
        
        print(f"Postgres returned {len(event_ids)} event IDs: {event_ids}")
        
        print("\n3. Querying Milvus...")
        if event_ids and len(event_ids) > 0:
            print(f"DEBUG: Calling query_milvus_by_list_id with event_ids: {event_ids}")
            milvus_result = query_milvus_by_list_id(event_ids)
        else:
            print(f"DEBUG: No event IDs found, falling back to semantic search with message: '{chat_request.message}'")
            milvus_result = query_milvus_by_vector_similarity(chat_request.message)
        
        print(f"DEBUG: Raw milvus_result type: {type(milvus_result).__name__}")
        
        if isinstance(milvus_result, str):
            print(f"DEBUG: milvus_result is a STRING (likely an error from Milvus): {milvus_result}")
        elif isinstance(milvus_result, list):
            print(f"DEBUG: milvus_result is a LIST. Number of items: {len(milvus_result)}")
            if milvus_result:
                print(f"DEBUG: First item in milvus_result: {milvus_result[0]}")
        else:
            print(f"DEBUG: milvus_result is of unexpected type: {type(milvus_result)}")

        print("\n4. Generating LLM Response...")
        llm_response = generate_llm_response(milvus_result)
        print(f"Final response: {llm_response}")
        
        print("\n=== Chat Pipeline Complete ===\n")
        
        return ChatResponse(response=llm_response)
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        print(f"❌ Error details: {str(e)}")
        print("\n=== Chat Pipeline Failed ===\n")
        return ChatResponse(response="Sorry, I encountered an error processing your request.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

