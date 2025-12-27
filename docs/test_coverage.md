# Test Coverage Documentation

This document lists all modules and components being tested in the functional tests of the Nuze Backend project.

## Integration Tests (API Level)

Integration tests verify the complete API endpoints work correctly with real database interactions.

| Module | File | Description | Responsibility |
|--------|------|-------------|----------------|
| **Auth API** | `test_auth_api.py` | Authentication endpoints | User signup (`POST /auth/signup`), login (`POST /auth/login`), token validation, error handling (duplicate emails, wrong passwords, invalid tokens) |
| **Feed API** | `test_feed_api.py` | Personalized feed endpoints | `GET /feed/` for authenticated users, exclusion of read articles, pagination, empty feed scenarios |
| **Feedback API** | `test_feedback_api.py` | User interaction endpoints | `POST /feedback/` for likes/dislikes/clicks, preference vector updates, invalid article handling |
| **Onboarding Flow** | `test_onboarding_flow.py` | End-to-end onboarding | Signup→onboarding→feed flow, preference vector initialization, demographics influence, `is_onboarded` flag |
| **Summary API** | `test_summary_api.py` | Daily summary endpoints | `GET /summary/today`, `POST /summary/generate`, empty article handling |
| **Users API** | `test_users_api.py` | User profile endpoints | `GET /me`, `GET/POST /me/preferences`, `POST /me/password`, `GET /me/read` |

---

## Unit Tests (Service Level)

Unit tests verify individual service classes work correctly in isolation.

| Module | File | Description | Responsibility |
|--------|------|-------------|----------------|
| **AuthService** | `test_auth_service.py` | Authentication logic | User creation with password hashing, duplicate email prevention, credential validation |
| **UserService** | `test_user_service.py` | User management | Get/update preferences, vector initialization from onboarding, demographics encoding, reading history |
| **FeedService** | `test_feed_service.py` | Feed generation | Personalized feed via cosine similarity, recency fallback, interacted article exclusion, pagination |
| **FeedbackService** | `test_feedback_service.py` | Feedback processing | Like/dislike/click recording, learning rate calculations, vector normalization, metadata conversion |
| **SummaryService** | `test_summary_service.py` | Summary management | Get existing summaries, generate new summaries via LLM, image URL injection, malformed JSON handling |
| **NLPService** | `test_nlp_service.py` | LLM integration | Article classification (10-dim vectors), article summarization, Ollama error handling, JSON/markdown cleanup |
| **IngestionService** | `test_ingestion_service.py` | Article ingestion | Ollama JSON parsing, category score extraction/normalization, dry-run mode, duplicate detection |

---

## Test Details

### AuthService
- `TestCreateUser`: User creation, duplicate email handling, password hashing verification
- `TestAuthenticateUser`: Successful authentication, wrong password, unknown email, data preservation

### UserService
- `TestGetUserPreferences`: Existing user, nonexistent user, null preference handling
- `TestUpdateUserPreferences`: Successful updates, nonexistent user handling
- `TestInitializeUserVector`: Basic initialization, age demographics, category preferences, metadata defaults
- `TestGetReadArticles`: Empty history, history retrieval, pagination

### FeedService
- `TestGetPersonalizedFeed`: No preferences fallback, similarity sorting, interacted exclusion, pagination, empty database
- `TestGetTopArticles`: No preferences fallback, similarity sorting, empty database

### FeedbackService
- `TestRecordFeedback`: Article not found error handling
- `TestCalculateUpdate`: Positive/negative feedback math, click learning rate ratio
- `TestHelperMethods`: Vector normalization, negative value handling, metadata conversion

### SummaryService
- `TestGetDailySummary`: Existing summary retrieval, not found handling
- `TestGenerateDailySummary`: No articles case, successful generation, image URL inclusion, malformed JSON handling

### NLPService
- `TestClassifyArticle`: Successful classification, error handling, nested JSON cleanup
- `TestSummarizeArticles`: Successful summarization, error fallback, markdown cleanup, preferences passing
- `TestNLPServiceInit`: Default and custom model initialization

### IngestionService
- `TestParseOllamaJson`: Valid JSON, markdown blocks, extra text, invalid JSON, nested categories
- `TestExtractCategoryScores`: Normalization, missing keys, already-normalized scores
- `TestCallOllama`: Empty input handling
- `TestProcessArticle`: Dry run mode, missing URL handling

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Integration Test Files | 6 |
| Unit Test Files | 7 |
| Total Test Classes | ~30 |
| Total Test Methods | ~80+ |
