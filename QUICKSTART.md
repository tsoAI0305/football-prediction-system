# Quick Start Guide

This guide will help you get the Football Prediction System up and running in minutes.

## Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ and PostgreSQL (for local development)

## Option 1: Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/tsoAI0305/football-prediction-system.git
   cd football-prediction-system
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY if you want LLM analysis (optional)
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **Load sample data (optional)**
   ```bash
   # Wait for the API to be ready, then run:
   pip install requests
   python scripts/populate_sample_data.py
   ```

## Option 2: Local Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/tsoAI0305/football-prediction-system.git
   cd football-prediction-system
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**
   ```bash
   # Install PostgreSQL and create database
   createdb football_prediction
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs

## Quick API Tour

### 1. Create a Team
```bash
curl -X POST "http://localhost:8000/teams/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manchester City",
    "league": "Premier League",
    "country": "England"
  }'
```

### 2. Create a Match
```bash
curl -X POST "http://localhost:8000/matches/" \
  -H "Content-Type: application/json" \
  -d '{
    "home_team_id": 1,
    "away_team_id": 2,
    "league": "Premier League",
    "season": "2023-24",
    "match_date": "2024-03-15T15:00:00",
    "home_odds": 2.1,
    "draw_odds": 3.4,
    "away_odds": 3.2
  }'
```

### 3. Generate Prediction
```bash
curl -X POST "http://localhost:8000/predictions/generate/1?include_llm_analysis=false"
```

### 4. View All Predictions
```bash
curl "http://localhost:8000/predictions/"
```

## Next Steps

- **Explore the API**: Visit http://localhost:8000/docs for interactive documentation
- **Customize**: Modify the ML models in `app/services/ml_predictor.py`
- **Add LLM Analysis**: Set up your Groq API key in `.env` for AI-powered insights
- **Deploy**: Use the Docker Compose setup for production deployment

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Troubleshooting

**Database connection issues:**
- Check that PostgreSQL is running
- Verify DATABASE_URL in .env file
- For Docker, ensure the db service is healthy

**API not starting:**
- Check port 8000 is not in use
- Verify all dependencies are installed
- Check logs: `docker-compose logs app`

**Tests failing:**
- Ensure test database is accessible
- Run: `pytest tests/ -v` for detailed output

## Support

For issues and questions:
- Check the [README.md](README.md) for detailed documentation
- Review API docs at http://localhost:8000/docs
- Open an issue on GitHub

## What's Next?

1. **Train Custom Models**: Replace heuristic predictions with trained XGBoost/LightGBM models
2. **Add More Data**: Integrate real web scrapers for live data
3. **Enhance Features**: Add more team statistics and match features
4. **Deploy to Cloud**: Use the Docker setup to deploy on AWS, GCP, or Azure
