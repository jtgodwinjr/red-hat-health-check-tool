# Contributing to Red Hat Health Check Tool

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm 10+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies API requests to the Django backend on port 8080.

### Running Tests

Backend:
```bash
cd backend
pytest -v
```

Frontend:
```bash
cd frontend
npm test
```

### Building the Container

```bash
docker build -t redhat-healthcheck .
docker run -p 8080:8080 -v healthcheck-data:/data redhat-healthcheck
```

## Code Style

- Backend: Follow PEP 8. Use type hints.
- Frontend: TypeScript strict mode. Follow PatternFly component patterns.

## Pull Requests

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass
4. Submit a PR with a clear description
