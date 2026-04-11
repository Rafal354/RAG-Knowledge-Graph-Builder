# Knowledge Graph Builder

An application for automatically building knowledge graphs from text articles using a Large Language Model and Neo4j.

Users upload articles through a web interface. The system extracts entities and relations, then builds and incrementally updates a knowledge graph stored in Neo4j.

## Architecture

```
Frontend (nginx)  →  FastAPI  →  PostgreSQL  (articles, graph versions)
                             →  Neo4j        (active knowledge graph)
                             →  LLM API      (entity and relation extraction)
```

## Requirements

- Docker + Docker Compose (recommended)
- Python 3.12+ (local setup)
- LLM API key

---

## Running with Docker

### 1. Configure environment variables

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

`.env` contents:

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=knowledge_base
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

OPENAI_API_KEY=sk-...
OPENAI_REQUEST=false        # true = real LLM call, false = mock response

LLM_MODEL=gpt-4o-mini
```

### 2. Start

```bash
docker compose up --build
```

### 3. Available addresses

| Address | Description |
|---------|-------------|
| `http://localhost` | Frontend — upload articles |
| `http://localhost:8000/docs` | Swagger UI (API documentation) |
| `http://localhost:7474` | Neo4j Browser — graph visualization |

### 4. Visualizing the graph in Neo4j Browser

Open `http://localhost:7474`, log in with credentials from `.env` and run:

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
```

---

## Running locally (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL running locally
- Neo4j running locally or via Neo4j Desktop

### 1. Virtual environment and dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` — set hosts to `localhost`:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=knowledge_base
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

OPENAI_API_KEY=sk-...
OPENAI_REQUEST=false

LLM_MODEL=gpt-4o-mini
```

### 3. Start the application

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`.

### 4. Frontend

Open `frontend/index.html` directly in your browser.

> Note: when running locally the frontend uses `/api/...` paths proxied by nginx — without Docker you need to temporarily change the URLs in `script.js` to `http://localhost:8000/...`.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Application status |
| `POST` | `/articles` | Add an article and update the graph |
| `GET` | `/articles` | List all articles |
| `GET` | `/articles/{id}` | Get an article |
| `DELETE` | `/articles/{id}` | Delete an article |
| `GET` | `/graphs` | Get the current graph |
| `GET` | `/graphs/{id}` | Get a specific graph version |
| `POST` | `/graphs/{id}` | Restore a specific graph version in Neo4j |
| `DELETE` | `/graphs/clean` | Clear the knowledge graph |

Full documentation: `http://localhost:8000/docs`
