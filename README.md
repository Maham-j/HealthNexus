# HealthNexus

**HealthNexus** is a Medical Knowledge Graph & Clinical Reasoning System. It
connects a LangChain agent to a Neo4j biomedical knowledge graph (PrimeKG),
letting users ask natural-language medical questions through OpenWebUI and
get grounded, cited answers — with full visibility into how the answer was
derived.

---

## What It Does

Given a biomedical question, the agent:

1. **Decides on its own** whether to query the Neo4j knowledge graph, look
   up similar past questions via FAISS (to help write a better Cypher
   query), both, or neither — no hardcoded tool order.
2. **Answers from the graph** when relevant data exists, and cites it.
3. **Falls back to general biomedical knowledge** when the graph doesn't
   have the answer — always clearly labeled as such, never presented as if
   it came from the graph.
4. **Labels mixed answers** — if part of a response comes from the graph
   and part from general knowledge, each part is marked separately.
5. **Remembers the conversation** — follow-up questions ("which of those
   are hereditary?", "summarize our conversation") resolve correctly using
   prior context.
6. **Shows its reasoning** in a collapsible "Thought" section in
   OpenWebUI — which tools it called, what it searched for, and what came
   back — before the final answer.
7. **Respects your model choice** — pick any supported model from
   OpenWebUI's dropdown, and that's the model that actually runs, end to
   end, through the full pipeline.

---

## Project Structure
```
healthnexus/
├── .env
├── .gitignore
├── Makefile
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entrypoint
│   ├── config.py                  # loads .env, settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── openai_routes.py       # /v1/models, /v1/chat/completions (OpenWebUI-facing)
│   │   ├── auth_routes.py         # /auth/login (JWT)
│   │   └── routes.py              # /health, /query/raw (JWT-protected)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── neo4j_connector.py     # Neo4jConnector — wraps the neo4j driver
│   │   ├── neo4j_tool.py          # Neo4j Cypher execution + schema description
│   │   ├── rag_tool.py            # FAISS RAG over the Excel example bank
│   │   ├── langchain_tools.py     # LangChain @tool wrappers (Neo4j + FAISS)
│   │   ├── langchain_agent.py     # SYSTEM_PROMPT, AgentExecutor, ask_agent()
│   │   └── chat_service.py        # chat(), get_models(), metadata bypass
│   └── models/
│       ├── __init__.py
│       └── schemas.py             # ChatCompletionRequest and related models
├── data/
│   └── PrimeKG_manual_databank.xlsx   # 30+ question/Cypher/response/finding examples
├── docs/
│   └── HealthNexus_LangChain_Migration.md   # issues found & fixed, with screenshots
├── images/                        # screenshots referenced in docs
└── scripts/
    └── check_neo4j_connection.py
```

## Architecture

```
            Browser
               │
               ▼
          OpenWebUI
               │
     OpenAI-compatible API
               │
               ▼
       FastAPI Backend  (/v1/models, /v1/chat/completions)
               │
               ▼
     LangChain AgentExecutor
               │
        ┌──────┴───────┐
        │              │
        ▼              ▼
  Neo4j Tool      FAISS RAG Tool
  (run_neo4j_      (fetch_similar_
   query)           queries)
        │              │
        ▼              ▼
  Neo4j (PrimeKG)   Excel example bank
                    (30+ Q&A pairs)
```

The agent decides at runtime which tool(s) to call — the FastAPI layer only
handles routing, model selection, and formatting; all reasoning and tool
orchestration lives in the LangChain agent.

---

## Tech Stack

- **API layer:** FastAPI, OpenAI-compatible `/v1` endpoints (streaming
  supported via SSE)
- **Orchestration:** LangChain (`create_tool_calling_agent` +
  `AgentExecutor`)
- **LLM:** Groq (model selectable per request — e.g. `openai/gpt-oss-120b`,
  `llama-3.3-70b-versatile`)
- **Knowledge graph:** Neo4j, loaded with PrimeKG
- **Retrieval:** FAISS + `sentence-transformers` over a manually curated
  Excel bank of question/Cypher/result/finding examples
- **Frontend:** OpenWebUI

---

## Features

### Autonomous tool use
No forced tool order. The agent decides whether to call the Neo4j tool, the
FAISS retrieval tool, both, or neither, based on the question.

### Grounded, cited answers
Every answer states its source — Neo4j graph, general knowledge, or both
(labeled separately when mixed). The agent won't stop at "the graph doesn't
have this" without still providing an answer from general knowledge.

### Fabrication guards
The agent won't invent biomedical mechanisms, causes, or classifications
that aren't explicitly supported by tool output — and won't fabricate
disease/syndrome names that don't exist in standard medical terminology.

### Multi-turn memory
Conversation history is passed to the agent on every turn, so follow-up
questions and full-conversation summaries work correctly.

### Chain-of-thought display
OpenWebUI shows a collapsible "Thought" section with the tool calls made
and their results, formatted as markdown (bold labels, fenced Cypher code
blocks) rather than raw Python/dict output.

### Model selection from OpenWebUI
The model is built per-request from whatever OpenWebUI sends — pick a
different model from the dropdown, and the agent actually runs on that
model, not a hardcoded default.

### Safe, bounded queries
Neo4j results are truncated with a note when a query matches more rows
than shown, preventing token-limit crashes on large result sets.

---

## Setup

### 1. Neo4j
Load the PrimeKG dataset into a running Neo4j instance. Set the connection
details in `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### 2. Groq API key
```
GROQ_API_KEY=your_groq_key
```

### 3. Install dependencies
```
pip install -r requirements.txt --break-system-packages
```

### 4. Run the backend
```
make dev
```
or directly:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. OpenWebUI
Run OpenWebUI via Docker:
```
docker run -d -p 3000:8080 --name open-webui -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```
In OpenWebUI: **Settings → Connections**, add your backend's OpenAI-compatible
endpoint:
```
http://host.docker.internal:8000/v1
```
Refresh models — your Groq-backed models should appear in the dropdown.

---

## Example Usage

**Graph-grounded question:**
> "What diseases are associated with TP53?"

Returns a list of diseases pulled directly from Neo4j, cited as such.

**Fallback to general knowledge:**
> "What is the mechanism of action of aspirin?"

Since the graph doesn't have a `drug_effect` entry for aspirin's mechanism,
the agent answers from general knowledge and clearly labels it.

**Mixed sources:**
> "Which of those are hereditary?" (as a follow-up)

The agent states what the graph *doesn't* know (no hereditary attribute on
disease nodes), then answers the classification from general knowledge —
each part labeled separately.

**Multi-turn memory:**
> "Summarize our conversation so far."

Uses the full chat history already passed to the agent — no separate
summarization tool needed.

---

## Known Limitations

- **Clickable citation modal** (like Gemini/ChatGPT's source-favicon UI)
  isn't achievable through an external OpenAI-compatible API — OpenWebUI's
  native citation UI requires running as an in-app Function/Pipe using
  `__event_emitter__`, which this architecture doesn't use.
- **No live web search** — general-knowledge answers are labeled as such
  rather than backed by a real citable URL, since they aren't the result of
  a live search.
- **Keyword-based filters are heuristics** — Cypher queries filtering by
  substrings like `CONTAINS 'syndrome'` are flagged in the tool description
  as weak text matches, not reliable classification.

---

## Project Documentation

See [`docs/HealthNexus_LangChain_Migration.md`](docs/HealthNexus_LangChain_Migration.md)
for the detailed history of issues found and fixed during the migration
from a manual, hardcoded tool-calling pipeline to the current LangChain
agent — including screenshots of before/after behavior.