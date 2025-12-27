# Nuze System Documentation

This directory contains the system architecture documentation for the Nuze backend.

## Files

| File | Description |
|------|-------------|
| [architecture_diagram.md](./architecture_diagram.md) | System architecture diagram showing all components and connections |
| [erd.md](./erd.md) | Entity Relationship Diagram for the database |
| [data_flow.md](./data_flow.md) | Data flow diagrams showing the main pipelines |
| [components.md](./components.md) | Detailed documentation of entities, boundaries, and controls |

## Quick Overview

**Tech Stack:**
- Backend: FastAPI (Python)
- Database: PostgreSQL with pgvector extension
- LLM: Ollama
- Frontend: React

**Core Features:**
- Personalized news feed using vector similarity
- AI-synthesized articles from multiple sources
- Daily personalized summaries
- Preference learning from user interactions
