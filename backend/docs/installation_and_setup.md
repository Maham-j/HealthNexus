# Installation & Setup

Complete setup guide for running HealthNexus locally.

## Prerequisites

- Python 3.11+
- Docker Desktop (for OpenWebUI)
- A running Neo4j instance (Desktop, AuraDB, or self-hosted)
- A Groq API key ([console.groq.com](https://console.groq.com))

---

## 1. Clone the Repository

```
git clone <repo-url>
cd healthnexus
```

---

## 2. Dataset — PrimeKG

This project uses [PrimeKG](https://github.com/mims-harvard/PrimeKG)
(Harvard, Zitnik lab) — a biomedical knowledge graph integrating 20 public
resources into over 17,000 diseases and 4 million relationships across ten
biological scales, including disease-drug indications, contraindications,
off-label uses, and symptom/phenotype connections. Free and open.

Download the **nodes** and **edges** files from the Harvard Dataverse
dataset page (DOI: [`10.7910/DVN/IXA7BM`](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM)).

Load them into your Neo4j instance — see
[github.com/mims-harvard/PrimeKG](https://github.com/mims-harvard/PrimeKG)
for loading tutorials and source code.

---

## 3. Backend Setup

### 3.1 Create a virtual environment

```
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 3.2 Install dependencies

```
pip install -r requirements.txt --break-system-packages
```

### 3.3 Configure environment variables

Create a `.env` file inside `backend/`:

```
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_neo4j_username
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j_database

GROQ_API_KEY=your_groq_key
```

### 3.4 Run the backend

```
make dev
```

or directly:

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for `Application startup complete` in the terminal — this confirms
both the Neo4j schema description and the FAISS RAG index have loaded
successfully.

---

## 4. Frontend Setup — OpenWebUI

### 4.1 Run OpenWebUI via Docker

```
docker run -d \
  -p 3000:8080 \
  --name open-webui \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### 4.2 Open OpenWebUI

Navigate to `http://localhost:3000` in your browser and create an account
(first launch) or log in.

### 4.3 Connect OpenWebUI to the backend

In OpenWebUI: **Settings → Connections → OpenAI API**, add a new connection
pointing to your backend:

```
http://host.docker.internal:8000/v1
```

The API key field can be any placeholder value (e.g. `dummy`) — the backend
doesn't check it.

### 4.4 Verify

Refresh the model list — you should see your Groq-backed models (e.g.
`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`) in the dropdown. Pick one
and ask a biomedical question to confirm the full pipeline works.

---

## 5. Optional — EDA Notebook

To explore the PrimeKG dataset directly:

```
cd notebooks
jupyter notebook
```

Open `PrimeKG_EDA.ipynb` and run all cells. It uses the same `.env`
credentials as the backend (points to `../backend/.env`).

---

## Troubleshooting

- **`AuthError: Unsupported authentication token`** — usually means the
  `.env` file wasn't found by `load_dotenv()`. Check the working directory
  the process was started from, or pass an explicit `dotenv_path`.
- **413 / token limit errors** — check that Neo4j query result truncation
  is working (`execute_neo4j_query`'s `max_results` cap); very large,
  un-truncated result sets can exceed the model's token budget.
- **Models missing or erroring in OpenWebUI dropdown** — some Groq models
  (embedding, audio, moderation models) aren't chat-capable and will error
  if selected; `get_models()` filters known non-chat models, but if a new
  one slips through, the backend returns a clear error message rather than
  crashing.
- **Slow first request** — the FAISS/embedding model and Neo4j schema
  description both load at startup (~30-60s total), not per-request; this
  is expected once at boot, not repeated on every chat message.
