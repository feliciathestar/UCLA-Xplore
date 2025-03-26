from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()

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


### Define data validation models ###
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


### Utility functions ###
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



### API routes ###

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



# Dummy functions to simulate your pipeline
def query_postgres(message: str):
    # Replace this with your actual PostgreSQL query
    return f"Data from PostgreSQL for '{message}'"

def query_milvus(data: str):
    # Replace this with your actual Milvus query logic
    return f"Semantic vector for data: {data}"

def generate_llm_response(milvus_result: str):
    # Replace this with your LLM integration logic
    return f"Concise response based on {milvus_result}"



# Chat endpoint – requires authentication
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, current_user: User = Depends(get_current_user)):
    # Pipeline: Postgres -> Milvus -> LLM
    postgres_data = query_postgres(chat_request.message)
    milvus_result = query_milvus(postgres_data)
    llm_response = generate_llm_response(milvus_result)
    return {"response": llm_response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

