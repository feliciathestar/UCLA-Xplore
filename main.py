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

# milvus connection
from pymilvus import connections, Collection
import openai

# Other imports
from datetime import datetime, timezone, timedelta
from typing import Optional


# Initialize FastAPI app
app = FastAPI()

# Add Milvus connection constants
MILVUS_ENDPOINT = "https://in03-360d7a6acbd9660.serverless.gcp-us-west1.cloud.zilliz.com"
MILVUS_TOKEN = "0655b3db6ad52e4419627358025db8c966d6de3929cf4894e14fcc54cc5d16252ec0ce468937a2f478cb9c09a5932dfdee73e180"
MILVUS_COLLECTION_NAME = "ucla_club_events"

# Add OpenAI constants
OPENAI_API_KEY = "your-openai-api-key"  # Replace with your actual key
EMBEDDING_MODEL = "text-embedding-ada-002"

# Initialize OpenAI and Milvus connections
openai.api_key = OPENAI_API_KEY

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

class ChatRequest(BaseModel):
    # Incoming chat message from user
    message: str

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

# Register endpoint 
@app.post("/auth/register", response_model=Token)
async def register(user: UserIn):
    """
    Register a new user with a hashed password.
    """
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    
    access_token = create_jwt(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Login endpoint
@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login a user and return an access token.
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_jwt(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


##########################
### Postgres Functions ###
##########################

def query_postgres(message: str):
    """
    Query PostgreSQL database based on user message.
    
    Args:
        message: User query string that will be parsed for event criteria
        
    Returns:
        String of comma-separated event IDs matching the criteria
    """
    try:
        load_dotenv()

        # Extract query parameters from message (this is simplified)
        # Below are pre-defined sample input data. In a real implementation, you'd use NLP or parsing to extract date/time info
        date = '2025-02-19'  
        start_time = '12:00:00' 
        end_time = '18:00:00' 

        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname="xploredb",
            user="postgres", 
            password=os.getenv('DB_PASSWORD'),
            host="localhost"
        )
        cur = conn.cursor()

        # Updated query to find events based on date AND time range
        query = """
        SELECT * FROM events 
        WHERE date = %s 
        AND start_time >= %s 
        AND end_time <= %s;
        """
        cur.execute(query, (date, start_time, end_time))
        matching_events = cur.fetchall()
        
        # Format results as concatenated event IDs
        event_ids = []
        for event in matching_events:
            # Extract just the event_id (first element in each tuple)
            event_id = event[0]
            event_ids.append(str(event_id))
        
        cur.close()
        conn.close()
        
        return event_ids
        
    except psycopg2.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Error processing query: {e}"


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

def query_milvus_by_list_ids(event_ids: list):
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

def generate_llm_response(milvus_result: str):
    # Replace this with your LLM integration logic
    return f"Concise response based on {milvus_result}"



# Chat endpoint – requires authentication
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, current_user: User = Depends(get_current_user)):
    # Pipeline: Postgres -> Milvus -> LLM
    event_ids = query_postgres(chat_request.message)
    milvus_result = query_milvus_by_list_ids(event_ids)
    llm_response = generate_llm_response(milvus_result)
    return {"response": llm_response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

