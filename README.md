<p align="center">
  <h1 align="center">📰 Nuze</h1>
  <p align="center">
    <strong>AI-Powered Personalized News Aggregator</strong>
  </p>
  <p align="center">
    A full-stack application that collects news from multiple sources, synthesizes articles using LLM, and delivers a personalized news feed that learns from your preferences.
  </p>
</p>

---

## ✨ Features

- **🤖 AI-Synthesized Articles** — Combines multiple news sources into unified, balanced articles using local LLM
- **🎯 Personalized Feed** — Vector-based recommendation using pgvector similarity matching
- **📚 Preference Learning** — User preferences evolve based on interactions (likes/dislikes)
- **📝 Daily Summaries** — LLM-generated personalized news digests
- **🔐 JWT Authentication** — Secure user registration and login
- **📊 10 News Categories** — Politics, Economy, Science, Health, Education, Culture, Religion, Sports, World Affairs, Opinion

---

## 📸 Screenshots

<p align="center">
  <img src="docs/screenshots/main_feed.png" alt="Nuze Main Feed" width="100%">
  <br>
  <em>Personalized News Feed - Your daily digest tailored to your interests</em>
</p>

<p align="center">
  <img src="docs/screenshots/article_view.png" alt="Article View" width="100%">
  <br>
  <em>AI-Synthesized Article View - Consolidated insights from multiple sources</em>
</p>

<p align="center" style="display: flex; justify-content: space-between;">
  <img src="docs/screenshots/daily_summary.png" alt="Daily Summary" width="48%">
  <img src="docs/screenshots/read_history.png" alt="Reading History" width="48%">
</p>
<p align="center">
  <em>Daily Summaries & Reading History</em>
</p>

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Client["Client Application"]
        WEB["React + Vite"]
    end

    subgraph Backend["FastAPI Backend"]
        API["REST API"]
        SCHEDULER["APScheduler"]
    end

    subgraph AI["AI/ML Layer"]
        OLLAMA["Ollama LLM"]
        MODELS["Custom Models"]
    end

    subgraph Data["Data Layer"]
        DB[("PostgreSQL + pgvector")]
        SCRAPERS["News Scrapers"]
    end

    WEB --> API
    API --> DB
    SCHEDULER --> SCRAPERS
    SCHEDULER --> OLLAMA
    SCRAPERS --> DB
    OLLAMA --> DB
    API --> OLLAMA
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | REST API framework |
| **PostgreSQL + pgvector** | Database with vector similarity search |
| **SQLAlchemy 2.0** | Async ORM |
| **Ollama** | Local LLM inference |
| **APScheduler** | Background task scheduling |
| **Passlib + python-jose** | Authentication (bcrypt + JWT) |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **Vite** | Build tool & dev server |
| **React Router** | Client-side routing |
| **Axios** | HTTP client |

### DevOps
| Technology | Purpose |
|------------|---------|
| **Docker Compose** | Container orchestration |
| **uv** | Python package management |
| **Pytest** | Testing framework |
| **Locust** | Load testing |

---

## 📁 Project Structure

```
nuze-backend/
├── app/                          # FastAPI application
│   ├── main.py                   # Application entrypoint
│   ├── database.py               # Database configuration
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py               # User entity
│   │   ├── article.py            # Raw article entity
│   │   ├── synthesized_article.py # AI-generated articles
│   │   ├── interaction.py        # User interactions
│   │   └── summary.py            # Daily summaries
│   ├── routers/                  # API endpoints
│   │   ├── auth.py               # /auth - Authentication
│   │   ├── users.py              # /me - User management
│   │   ├── feed.py               # /feed - Personalized feed
│   │   ├── summary.py            # /summary - Daily summaries
│   │   ├── feedback.py           # /feedback - Preference updates
│   │   ├── interactions.py       # /interactions - Like/dislike
│   │   └── ingestion.py          # /ingest - Manual triggers
│   ├── services/                 # Business logic
│   │   ├── nlp_service.py        # LLM integration
│   │   ├── feed_service.py       # Feed generation
│   │   ├── feedback_service.py   # Preference learning
│   │   ├── ingestion_service.py  # Article ingestion
│   │   ├── summary_service.py    # Summary generation
│   │   └── scheduler.py          # Background tasks
│   └── schemas/                  # Pydantic models
├── frontend/                     # React application
│   └── src/
│       ├── components/           # React components
│       │   ├── Article.jsx       # Article display
│       │   ├── DailySummary.jsx  # Summary view
│       │   ├── Onboarding.jsx    # Category selection
│       │   ├── Preferences.jsx   # Preference visualization
│       │   └── Profile.jsx       # User settings
│       └── api.js                # API client
├── scrapers/                     # News source scrapers
│   ├── new_bbc_scraper.py
│   ├── new_cnn_scraper.py
│   ├── new_foxnews_scraper.py
│   ├── new_nytimes_scraper.py
│   └── new_sky_news_scraper.py
├── scripts/
│   ├── init/                     # Initialization scripts
│   │   ├── init.sql              # Database extensions
│   │   ├── init_ollama.sh        # Ollama setup
│   │   └── ollama-models/        # Custom LLM models
│   ├── daily_cluster.py          # Article synthesis job
│   └── daily_ingest.py           # Article ingestion job
├── tests/                        # Test suites
├── docs/                         # Documentation
└── docker-compose.yml            # Container orchestration
```

---

## 🚀 Quick Start

### 🌐 Live Demo

The application is already deployed and running at **[nuze.dpdns.org](https://nuze.dpdns.org)**.

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU with atleast 24GB VRAM (for Ollama)

### 1. Clone & Install

```bash
git clone <repository-url>
cd nuze-backend
```

### 2. Choose Your Mode

The application can run in two modes:

| Mode | Script | Use Case |
|------|--------|----------|
| **Production** | `./run-prod.sh` | Connects to the live API server (`api.nuze.dpdns.org`) and production database. Use this to interact with real data. |
| **Development** | `./run-dev.sh` | Connects to local backend (`localhost:8000`) with hot reload. Use this for frontend development and testing. |

> [!IMPORTANT]
> To communicate with the actual published server and database that we are running, run **production mode** (`./run-prod.sh`).
> Development mode uses a local backend and is intended for local development only.

```bash
# Production mode - connects to live API
./run-prod.sh

# Development mode - local backend with hot reload
./run-dev.sh
```

### 3. Access the Application

| Mode | Frontend | Backend API | API Docs |
|------|----------|-------------|----------|
| Production | http://localhost:5173 | https://api.nuze.dpdns.org | https://api.nuze.dpdns.org/docs |
| Development | http://localhost:5174 | http://localhost:8000 | http://localhost:8000/docs |

### 4. Initial Setup (Development Mode Only)

When running in development mode, on first run the system will:
1. Initialize PostgreSQL with pgvector extension
2. Pull and configure Ollama models (phi4 and Qwen2.5 base models + custom models)
3. Create database tables via SQLAlchemy

---

## 🔄 Data Flow

### 1. Content Ingestion
```
News Sources → Scrapers → NLP Classification → Articles DB
```
Scheduled task scrapes articles from 5 news sources, classifies them into a 10-dimensional category vector using LLM.

### 2. Article Synthesis
```
Similar Articles → Clustering → LLM Synthesis → SynthesizedArticles DB
```
Daily job groups similar articles and generates balanced, unified articles.

### 3. Feed Generation
```
User Request → Vector Similarity (user preferences ↔ article categories) → Ranked Feed
```
Uses pgvector's cosine similarity to match user preferences with article category vectors.

### 4. Preference Learning
```
User Interaction → Feedback Service → Vector Update → User Preferences
```
Likes/dislikes adjust the user's 10-dimensional preference vector to improve future recommendations.

---

## 🧠 Custom LLM Models

Three custom Ollama models built on phi4:

| Model | Purpose |
|-------|---------|
| `news-classifier` | Classifies articles into 10 categories with confidence scores |
| `news-combiner` | Synthesizes multiple articles into a unified piece |
| `news-summarizer` | Generates personalized daily summaries |

---

## 📰 News Categories

The system uses 10 categories for article classification and user preferences:

1. Politics & Law
2. Economy & Business
3. Science & Technology
4. Health & Wellness
5. Education & Society
6. Culture & Entertainment
7. Religion & Belief
8. Sports
9. World & International Affairs
10. Opinion & General News

---

## 🔗 Key Code References

### Core Algorithms

| Algorithm | File | Description |
|-----------|------|-------------|
| **K-Means Clustering** | [`scripts/daily_cluster.py#L148-L154`](scripts/daily_cluster.py#L148-L154) | Groups similar articles by category vectors for synthesis. Uses `sklearn.KMeans` to cluster articles before LLM combination. |
| **Cosine Distance Ranking** | [`app/services/feed_service.py#L132-L141`](app/services/feed_service.py#L132-L141) | Ranks articles using pgvector's `cosine_distance()` between user preference vector and article category scores. |
| **Preference Learning** | [`app/services/feedback_service.py#L137-L178`](app/services/feedback_service.py#L137-L178) | Updates user preference vector based on interactions. Uses weighted decay: `new_pref = α × current_pref + (1-α) × article_vector` |
| **Summary Validation Loop** | [`app/services/nlp_service.py#L102-L137`](app/services/nlp_service.py#L102-L137) | 3-attempt retry loop with JSON validation for LLM summary generation. |
| **LLM Output Validation** | [`app/services/llm_validator.py#L1-L215`](app/services/llm_validator.py#L1-L215) | Validates LLM JSON responses against expected schema (categories, content types, scores). |

### LLM Model Definitions

| Model | File | Purpose |
|-------|------|---------|
| **Article Classifier** | [`scripts/init/ollama-models/news-cls-modfile`](scripts/init/ollama-models/news-cls-modfile) | System prompt for classifying articles into 10 categories with normalized scores summing to 5.0. |
| **Article Combiner** | [`scripts/init/ollama-models/news-combiner-modfile`](scripts/init/ollama-models/news-combiner-modfile) | Synthesizes multiple articles into one unified piece. Includes topic matching rules to decide which articles to combine. |
| **Daily Summarizer** | [`scripts/init/ollama-models/news-summarizer-modfile`](scripts/init/ollama-models/news-summarizer-modfile) | Generates personalized daily summaries with user preference integration. |

### Database Models & Vectors

| Component | File | Description |
|-----------|------|-------------|
| **User Preferences Vector** | [`app/models/user.py#L20`](app/models/user.py#L20) | 10-dimensional pgvector for category preferences. |
| **Article Category Scores** | [`app/models/article.py`](app/models/article.py) | 10-dimensional pgvector for article classification. |
| **Synthesized Article** | [`app/models/synthesized_article.py`](app/models/synthesized_article.py) | LLM-generated combined articles with source tracking. |
| **User Interactions** | [`app/models/interaction.py`](app/models/interaction.py) | Tracks likes/dislikes for preference learning. |

### Key Services

| Service | File | Responsibility |
|---------|------|----------------|
| **Feed Service** | [`app/services/feed_service.py`](app/services/feed_service.py) | Personalized feed generation using vector similarity. |
| **Feedback Service** | [`app/services/feedback_service.py`](app/services/feedback_service.py) | Preference vector updates from user interactions. |
| **NLP Service** | [`app/services/nlp_service.py`](app/services/nlp_service.py) | Ollama LLM integration for classification and summarization. |
| **Summary Service** | [`app/services/summary_service.py`](app/services/summary_service.py) | Daily summary generation with status tracking. |
| **Scheduler** | [`app/services/scheduler.py`](app/services/scheduler.py) | APScheduler jobs for ingestion (06:00/18:00 UTC) and clustering. |

### Background Jobs

| Job | File | Schedule |
|-----|------|----------|
| **Daily Ingestion** | [`scripts/daily_ingest.py`](scripts/daily_ingest.py) | Scheduled via [`app/services/scheduler.py#L100-L110`](app/services/scheduler.py#L100-L110) at 06:00 and 18:00 UTC. |
| **Daily Clustering** | [`scripts/daily_cluster.py`](scripts/daily_cluster.py) | Runs after ingestion completes. Groups and synthesizes articles. |

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/unit/test_nlp_service.py
```

### Load Testing
```bash
cd tests/load
locust -f locustfile.py
```

---

## 📊 Evaluation

Generate offline evaluation metrics for the recommendation system:

```bash
python experiments/evaluation_report.py
```

Outputs `experiments/evaluation_report.md` with per-user and aggregate metrics.

---

## 🔧 Development

### Running Locally (without Docker)

```bash
# Backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `OLLAMA_HOST` | Ollama server URL | `http://ollama:11434` |
| `VITE_API_URL` | Frontend API URL | `http://localhost:8000` |

### Frontend Development Modes

The frontend can run in **production** or **development** mode:

| Mode | Command | Frontend URL | API URL | Description |
|------|---------|--------------|---------|-------------|
| **Production** | `./run-prod.sh` | http://localhost:5173 | `https://api.nuze.dpdns.org` | Nginx serving static build |
| **Dev (Docker)** | `./run-dev.sh` | http://localhost:5174 | `http://localhost:8000` | Vite dev server with hot reload |
| **Dev (Local)** | `cd frontend && npm run dev` | http://localhost:5173 | `http://localhost:8000` | Vite dev server locally |

---

## 📄 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | User registration |
| POST | `/auth/login` | User login (returns JWT) |
| GET | `/me` | Get current user profile |
| PUT | `/me` | Update user profile |
| POST | `/me/onboard` | Set initial preferences |
| GET | `/feed` | Get personalized article feed |
| GET | `/summary` | Get today's personalized summary |
| POST | `/interactions` | Record like/dislike |
| POST | `/ingest/run` | Trigger manual ingestion |

---

## 📚 Documentation

Detailed documentation is available in the `/docs` directory:

- [System Architecture](docs/system_architecture.md) — Full architecture diagrams
- [Components](docs/components.md) — Entity and service descriptions
- [ERD](docs/erd.md) — Database entity relationships
- [Data Flow](docs/data_flow.md) — Data pipeline diagrams

---

## 📜 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.