# football-prediction-system
AI-powered football match prediction system with ML analysis and betting insights

## 📂 Project Structure

This repository contains a comprehensive football prediction system:

- **`backend/`** - FastAPI backend API with ML predictions and LLM analysis
  - See [backend/README.md](backend/README.md) for detailed documentation

## 🚀 Quick Start

```bash
# Navigate to backend directory
cd backend

# Start all services with Docker
./start.sh

# Or manually:
docker compose up -d

# Access the API at http://localhost:8000/docs
```

## 📚 Documentation

- [Backend API Documentation](backend/README.md) - Complete backend API guide
- [API Reference](http://localhost:8000/docs) - Interactive Swagger UI (after starting)

## 🛠️ Features

- ✅ **RESTful API** - FastAPI-based backend
- ✅ **AI Predictions** - Machine learning models (XGBoost/LightGBM)
- ✅ **Database** - PostgreSQL with SQLAlchemy ORM
- ✅ **Caching** - Redis for performance
- ✅ **LLM Integration** - Deep analysis using language models
- ✅ **Docker Support** - One-command deployment
- ✅ **Testing** - Comprehensive test suite

## 🎯 Next Steps

1. Clone the repository
2. Follow the [Backend Setup Guide](backend/README.md#-quick-start)
3. Explore the [API Documentation](http://localhost:8000/docs)

## 📝 License

MIT License

