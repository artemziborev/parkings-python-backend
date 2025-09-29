# Parkings

A system for searching and displaying parking spots in Moscow.

## Architecture

- **Backend**: Python (FastAPI) - API server
- **Frontend**: React - web interface  
- **Database**: MongoDB - parking data storage

## Quick Start

### Using Docker Compose (recommended)

1. Make sure Docker and Docker Compose are installed
2. Navigate to the `python/` folder
3. Start all services:

```bash
cd python
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- MongoDB on port 27018
- Backend API on port 3847

### Running Frontend

1. Navigate to the `parrot-frontend/` folder
2. Install dependencies and start:

```bash
cd parrot-frontend
npm install
npm start
```

Frontend will be available at http://localhost:3000

### Running Backend separately (for development)

1. Make sure Python 3.13+ is installed
2. Start MongoDB via Docker:

```bash
cd python
docker-compose -f docker-compose.dev.yml up mongodb
```

3. Set up Python environment and run backend:

```bash
cd python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m parking.main
```

## API Endpoints

- `GET /api/v1/mos_parking/parking?lat={lat}&long={long}&limit={limit}&distance={distance}` - search parkings by coordinates
- `GET /api/v1/mos_parking/parking/search?name={name}&limit={limit}` - search parkings by name
- `GET /api/v1/mos_parking/parking/{id}` - get parking by ID
- `POST /api/v1/mos_parking/sync` - force data synchronization
- `GET /health` - health check
- `GET /docs` - Swagger API documentation

## Configuration

- Backend configuration: Environment variables (see `env.example`)
- Frontend automatically connects to backend at `http://localhost:3847`

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Key variables:
- `MONGODB__ADDRESS` - MongoDB connection string
- `MONGODB__DATABASE` - Database name
- `PARKING_DATA_SOURCE__URL` - External API URL
- `HTTP_SERVER__PORT` - Backend port

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for full documentation.

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed API reference.

## Troubleshooting

### Frontend can't see backend

1. Make sure backend is running on port 3847
2. Check for CORS errors in browser console
3. Open http://localhost:3847/docs to verify API is working

### MongoDB connection

1. Check that MongoDB container is running: `docker ps`
2. Check logs: `docker-compose -f docker-compose.dev.yml logs mongodb`

### Port conflicts

If ports are busy, change them in:
- Environment variables (backend)
- `python/docker-compose.dev.yml` (MongoDB)
- `parrot-frontend/src/App.js` constant `API_BASE_URL` (frontend)

### Python environment issues

1. Make sure you're using Python 3.13+
2. Activate virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## Development

### Running tests

```bash
cd python
source venv/bin/activate
pytest tests/ -v
```

### Code formatting

```bash
cd python
source venv/bin/activate
black parking/ tests/
isort parking/ tests/
```

### Type checking

```bash
cd python
source venv/bin/activate
mypy parking/
```

## Project Structure

```
python/
├── parking/                 # Main application code
│   ├── application/        # Use cases and interfaces
│   ├── domain/            # Domain models
│   ├── infrastructure/    # External dependencies
│   ├── main.py           # Application entry point
│   └── sync_parkings.py  # Data synchronization utility
├── tests/                 # Test suite
├── config/               # Configuration files
├── docker-compose.dev.yml # Development environment
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
├── pyproject.toml      # Project metadata
├── env.example         # Environment variables template
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## License

This project is licensed under the MIT License.