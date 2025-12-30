# Cabin Rentals Backend API

FastAPI backend for the Cabin Rentals of Georgia platform.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/api/docs`

## Project Structure

- `app/main.py` - FastAPI application entry point
- `app/config.py` - Configuration management
- `app/api/v1/` - API route handlers
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic validation schemas
- `app/services/` - Business logic services
- `app/db/` - Database utilities and migrations

## Development

- Run tests: `pytest`
- Format code: `black .`
- Type check: `mypy app`

