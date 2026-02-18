# Football Prediction System

AI-powered football match prediction system with ML analysis and betting insights using FastAPI, PostgreSQL, XGBoost, LightGBM, and Groq LLM.

## Features

- **RESTful API** - Complete REST API for matches, predictions, and history
- **ML Predictions** - XGBoost and LightGBM ensemble models for match outcome prediction
- **LLM Analysis** - Groq-powered AI analysis and betting insights
- **Database** - PostgreSQL with SQLAlchemy ORM
- **Web Scrapers** - Automated data collection for standings and results
- **Docker Support** - Complete Docker Compose setup for easy deployment
- **Comprehensive Tests** - Full test suite with pytest

## Tech Stack

- **Backend**: FastAPI 0.109.0
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **ML Models**: XGBoost 2.0.3, LightGBM 4.3.0, scikit-learn 1.4.0
- **LLM**: Groq API integration
- **Web Scraping**: BeautifulSoup4, Requests
- **Testing**: pytest, pytest-asyncio
- **Deployment**: Docker, Docker Compose

## Project Structure

```
football-prediction-system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── match.py
│   │   ├── prediction.py
│   │   ├── team.py
│   │   └── history.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── match.py
│   │   ├── prediction.py
│   │   ├── team.py
│   │   └── history.py
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── matches.py
│   │   ├── predictions.py
│   │   └── history.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── ml_predictor.py    # ML prediction service
│   │   └── llm_analyzer.py    # LLM analysis service
│   └── scrapers/               # Web scrapers
│       ├── __init__.py
│       ├── standings_scraper.py
│       └── results_scraper.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_matches.py
│   └── test_ml_service.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/tsoAI0305/football-prediction-system.git
cd football-prediction-system
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY if you want LLM analysis
```

3. Start the services:
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/tsoAI0305/football-prediction-system.git
cd football-prediction-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database and configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Matches API
- `GET /matches/` - List all matches
- `GET /matches/{match_id}` - Get specific match
- `POST /matches/` - Create new match
- `PUT /matches/{match_id}` - Update match results
- `DELETE /matches/{match_id}` - Delete match

#### Predictions API
- `GET /predictions/` - List all predictions
- `GET /predictions/{prediction_id}` - Get specific prediction
- `POST /predictions/` - Create manual prediction
- `POST /predictions/generate/{match_id}` - Generate ML prediction for a match

#### History API
- `GET /history/` - List prediction history
- `GET /history/{history_id}` - Get specific history entry
- `GET /history/stats/accuracy` - Get prediction accuracy statistics

## Usage Examples

### Create Teams and Match

```python
import requests

# Create home team
home_team = {
    "name": "Manchester City",
    "league": "Premier League",
    "country": "England"
}
response = requests.post("http://localhost:8000/teams/", json=home_team)
home_team_id = response.json()["id"]

# Create away team
away_team = {
    "name": "Liverpool",
    "league": "Premier League",
    "country": "England"
}
response = requests.post("http://localhost:8000/teams/", json=away_team)
away_team_id = response.json()["id"]

# Create match
match = {
    "home_team_id": home_team_id,
    "away_team_id": away_team_id,
    "league": "Premier League",
    "season": "2023-24",
    "match_date": "2024-03-15T15:00:00",
    "home_odds": 2.1,
    "draw_odds": 3.4,
    "away_odds": 3.2
}
response = requests.post("http://localhost:8000/matches/", json=match)
match_id = response.json()["id"]
```

### Generate ML Prediction

```python
import requests

# Generate prediction with LLM analysis
response = requests.post(
    f"http://localhost:8000/predictions/generate/{match_id}",
    params={"include_llm_analysis": True}
)
prediction = response.json()

print(f"Home win: {prediction['home_win_probability']*100:.1f}%")
print(f"Draw: {prediction['draw_probability']*100:.1f}%")
print(f"Away win: {prediction['away_win_probability']*100:.1f}%")
print(f"LLM Analysis: {prediction['llm_analysis']}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_matches.py

# Run with verbose output
pytest -v
```

## Configuration

Environment variables (set in `.env` file):

- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key for LLM analysis (optional)
- `PORT` - Application port (default: 8000)
- `DEBUG` - Debug mode (default: true)

## ML Models

The system uses an ensemble of ML models:

1. **XGBoost** - Gradient boosting model for match outcome prediction
2. **LightGBM** - Fast gradient boosting framework
3. **Heuristic Model** - Fallback statistical model when ML models aren't trained

### Features Used

- Goals per game (home/away)
- Goals against per game (home/away)
- Win rate (home/away)
- Points per game (home/away)
- Relative metrics (differences between teams)

## LLM Analysis

The system integrates with Groq API for AI-powered match analysis:

- Match outcome analysis
- Key factors influencing predictions
- Team strengths and weaknesses
- Betting insights and value bets

## Web Scrapers

Template scrapers are provided for:

- **League Standings** - Team statistics and rankings
- **Match Results** - Historical match data
- **Upcoming Fixtures** - Future match schedules

Note: Customize scrapers based on your data source.

## Development

### Adding New Features

1. Create models in `app/models/`
2. Create schemas in `app/schemas/`
3. Add routers in `app/routers/`
4. Implement services in `app/services/`
5. Write tests in `tests/`

### Database Migrations

Using Alembic for migrations:

```bash
# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastAPI for the excellent web framework
- XGBoost and LightGBM for ML capabilities
- Groq for LLM integration
- PostgreSQL for reliable data storage
