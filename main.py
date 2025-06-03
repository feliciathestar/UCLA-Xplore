# FastAPI 
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# authentication and authorization
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# database connection
import psycopg2
import os
from dotenv import load_dotenv
# Remove pymilvus imports, use requests instead
import requests
import json
import openai
import numpy as np

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
MILVUS_CLUBS_COLLECTION_NAME = "ucla_clubs"

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
    """
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
        
        # Handle direct time slots from UI
        if direct_time_slots:
            for slot in direct_time_slots:
                if hasattr(slot, 'date'):
                    dates.append(slot.date)
                    time_slots.append({
                        'date': slot.date,
                        'start_time': slot.start_time,
                        'end_time': slot.end_time
                    })
        
        # Handle parsed parameters from natural language
        if params:
            if 'dates' in params:
                dates.extend(params['dates'])
            if 'time_slots' in params:
                time_slots.extend(params['time_slots'])
        
        # If no specific dates/times, return empty list
        if not dates and not time_slots:
            return []
        
        # Database connection
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432),
            sslmode=os.getenv("DB_SSLMODE", "require")
        )
        
        cur = conn.cursor()
        
        # Build query based on available parameters
        query_conditions = []
        query_params = []
        
        if dates:
            date_placeholders = ','.join(['%s'] * len(dates))
            query_conditions.append(f"DATE(event_start_time) IN ({date_placeholders})")
            query_params.extend(dates)
        
        if time_slots:
            time_conditions = []
            for slot in time_slots:
                time_conditions.append("(DATE(event_start_time) = %s AND TIME(event_start_time) >= %s AND TIME(event_start_time) <= %s)")
                query_params.extend([slot['date'], slot['start_time'], slot['end_time']])
            if time_conditions:
                query_conditions.append(f"({' OR '.join(time_conditions)})")
        
        if not query_conditions:
            return []
        
        query = f"""
        SELECT event_id FROM events 
        WHERE {' AND '.join(query_conditions)}
        ORDER BY event_start_time
        """
        
        cur.execute(query, query_params)
        matching_events = cur.fetchall()
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

def query_milvus_by_vector_similarity(query_text):
    """
    Query Milvus database for vector similarity search using REST API.
    
    Args:
        query_text: The text to search for similar events/clubs
        
    Returns:
        List of matching events/clubs or error string
    """
    try:
        # Initialize OpenAI client to get embeddings
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Get embedding for the query text
        embedding_response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=query_text
        )
        query_vector = embedding_response.data[0].embedding
        
        # Prepare search request for Milvus
        search_data = {
            "collectionName": MILVUS_COLLECTION_NAME,
            "vector": query_vector,
            "limit": 10,
            "outputFields": ["event_name", "event_tags", "event_programe", "event_location", "event_description", "type"]
        }
        
        headers = {
            "Authorization": f"Bearer {MILVUS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Make request to Milvus
        response = requests.post(
            f"{MILVUS_ENDPOINT}/v1/vector/search",
            headers=headers,
            json=search_data
        )
        
        if response.status_code == 200:
            results = response.json()
            return results.get("data", [])
        else:
            return f"Milvus search failed with status {response.status_code}"
            
    except Exception as e:
        print(f"Error querying Milvus: {e}")
        return f"Error searching for similar content: {str(e)}"

def generate_llm_response(milvus_result, event_ids=None, user_message=""):
    """
    Generate a natural language response about events using OpenAI's API.
    
    Args:
        milvus_result: List of event details from Milvus query or error string
        event_ids: List of event IDs from PostgreSQL query (optional)
        user_message: The original user question for context
        
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
            return "I couldn't find any events or clubs matching your criteria. Perhaps try a different date, time, or interests? You can also ask about specific activities, academic programs, or social events at UCLA."
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Format event information for the prompt
        events_text = ""
        events_count = 0
        clubs_count = 0
        
        for item in milvus_result:
            item_type = item.get('type', 'event')
            
            if item_type == 'club':
                clubs_count += 1
                events_text += f"""
Club: {item.get('event_name', 'N/A')}
Category: {item.get('event_tags', 'N/A')}
Description: {item.get('event_description', 'N/A')}
Email: {item.get('email', 'N/A')}
Website: {item.get('website', 'N/A')}
---
"""
            else:
                events_count += 1
                events_text += f"""
Event: {item.get('event_name', 'N/A')}
Tags: {item.get('event_tags', 'N/A')}
Program: {item.get('event_programe', 'N/A')}
Location: {item.get('event_location', 'N/A')}
Description: {item.get('event_description', 'N/A')}
---
"""
        
        # Create context-aware system prompt
        system_prompt = """You are a knowledgeable UCLA campus assistant who helps students discover events, clubs, and activities. 
        Your goal is to provide helpful, personalized recommendations based on what the user is looking for.
        
        Guidelines:
        - Analyze the user's question to understand what they're really asking for
        - Provide a conversational, friendly response that directly addresses their needs
        - Highlight the most relevant and interesting options first
        - Include practical details like locations, contact info when helpful
        - If showing multiple options, group them logically and explain why they might be good fits
        - Make your response engaging and encourage further exploration
        - Don't just list information - synthesize and recommend based on their interests"""

        user_prompt = f"""
        User Question: "{user_message}"
        
        Found {events_count} events and {clubs_count} clubs:
        {events_text}
        
        Please provide a helpful, conversational response that addresses the user's specific question and highlights the most relevant recommendations.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return f"I found some relevant events and clubs, but I'm having trouble formatting the response right now. Please try again in a moment."

# Add missing API endpoints
@app.post("/auth/register")
async def register(user: UserIn):
    """Register a new user"""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    
    return {"message": "User registered successfully"}

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns JWT token"""
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Extract parameters from natural language
        params = extract_query_parameters(request.message)
        
        # Convert timeSlots to direct format if provided
        direct_time_slots = None
        if request.timeSlots:
            direct_time_slots = request.timeSlots
        
        # Query postgres for time-based filtering
        event_ids = query_postgres(params, direct_time_slots)
        
        # Query milvus for semantic similarity
        milvus_result = query_milvus_by_vector_similarity(request.message)
        
        # Generate response
        response = generate_llm_response(milvus_result, event_ids, request.message)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return ChatResponse(response="I'm sorry, I encountered an error processing your request. Please try again.")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the UCLA-Xplore API!",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "register": "/auth/register",
            "login": "/auth/login"
        }
    }

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI application is starting up...")
    logger.info(f"Environment variables loaded: {bool(os.getenv('OPENAI_API_KEY'))}")
    logger.info(f"Database configured: {bool(os.getenv('DB_HOST'))}")
    logger.info(f"Milvus configured: {bool(os.getenv('MILVUS_ENDPOINT'))}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🔄 FastAPI application is shutting down...")

if __name__ == "__main__":
    import uvicorn
    # Railway sets the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

