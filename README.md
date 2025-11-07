# UCLA-Xplore

A chatbot that answers questions about on-campus events and extracurricular activities, with an additional graphic time availability selector.


## Project Structure

```
UCLA-Xplore/
├── backend/           # Backend API code
├── frontend/          # Frontend Next.js application
├── data/              # Data loading scripts 
├── docs/              # Documentation
├── main.py            # FastAPI application entry point
├── requirements.txt   # Python dependencies
└── .env               # Environment variables (not in git)
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Node.js 18+ (for frontend)
- pnpm (for frontend package management)

### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/UCLA-Xplore.git
   cd UCLA-Xplore
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. Start the backend server
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at http://127.0.0.1:8000

### Frontend Setup

1. Navigate to the frontend directory
   ```bash
   cd frontend
   ```

2. Install dependencies
   ```bash
   pnpm install
   ```

3. Start the development server
   ```bash
   pnpm dev
   ```
   The frontend will be available at http://localhost:3000

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Database Setup

1. Create a PostgreSQL database named `xploredb`
2. Run the database migration scripts in `data/`

## License

[MIT](LICENSE)
