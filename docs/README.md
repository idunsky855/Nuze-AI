# Nuze System Documentation

This directory contains the system architecture documentation for the Nuze backend.

## Documentation Structure

### Architecture & Design
| File | Description |
|------|-------------|
| [system_architecture.md](./system_architecture.md) | Comprehensive system architecture documentation |
| [architecture_diagram.md](./architecture_diagram.md) | System architecture diagram showing all components |
| [components.md](./components.md) | Detailed documentation of entities, boundaries, and controls |

### Data & Database
| File | Description |
|------|-------------|
| [erd.md](./erd.md) | Entity Relationship Diagram for the database |
| [data_flow.md](./data_flow.md) | Data flow diagrams showing the main pipelines |
| [Categories.md](./Categories.md) | News category definitions |

### Testing
| File | Description |
|------|-------------|
| [test_plan.md](./test_plan.md) | Test scenarios for main use cases (Hebrew) |
| [test_coverage.md](./test_coverage.md) | Test coverage documentation - all tested modules and components |

### Class Diagrams
| File | Description |
|------|-------------|
| [class_diagrams/](./class_diagrams/) | All class diagrams |
| [Complete System](./class_diagrams/class_diagram.md) | Full system class diagram |
| [Data Layer](./class_diagrams/class_diagram_data_layer.md) | SQLAlchemy models |
| [API Layer](./class_diagrams/class_diagram_api_layer.md) | Pydantic schemas |
| [Business Layer](./class_diagrams/class_diagram_business_layer.md) | Service classes |
| [External Layer](./class_diagrams/class_diagram_external_layer.md) | Scrapers & utilities |

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
