# HealthNexus — Medical Knowledge Graph & Clinical Reasoning System

GraphRAG over a Neo4j-backed medical knowledge graph (PrimeKG), with two
LLM interaction modes:

1. **GraphRAG QA** (`/ask/graphrag`) — we retrieve relevant graph context
   ourselves, then the LLM reasons over that context to answer.
2. **Cypher generation** (`/ask/cypher`) — the LLM writes its own Cypher
   query, we run it against Neo4j, and the LLM turns the table result
   into a plain-English answer.

A raw endpoint (`/query/raw`) is also included for manual Cypher testing
via Postman, bypassing the LLM entirely.

## Setup

```bash
make install        # creates venv, installs deps, copies .env.example -> .env
# edit .env with your real Neo4j + LLM credentials
make check-neo4j     # confirms the app can reach your Neo4j instance
make dev             # runs the API with auto-reload on http://localhost:8000
```

Interactive API docs (Swagger) once running: `http://localhost:8000/docs`

## Free LLM API research 



| Provider | Model(s) | Free limit | Notes |
|---|---|---|---|
| **Google AI Studio (Gemini)** | Gemini 2.5 Flash | ~1,500 req/day, 1M context | Best overall free frontier model; multimodal (text/image/PDF). Data may be used for training on free tier. |
| **Groq** | Llama 3.3 70B, Qwen, DeepSeek-R1 | ~30 req/min, 1,000 req/day | Fastest inference (custom LPU hardware); does not train on your prompts. |
| **Cerebras** | Llama 3.3 70B + others | ~1M tokens/day | Very high daily volume; model catalog changes often — don't hardcode a single model name. |
| **OpenRouter** | 30+ open models (aggregator) | 20 req/min, 50 req/day (up to 1,000/day after $10 lifetime spend) | One API key for many models; useful fallback option. |
| **GitHub Models** | GPT-style + Llama endpoints | Rate-limited, free for any GitHub account | Closest thing to a free "GPT-style" endpoint. |

**Recommendation for this project:** default to **Gemini** (`LLM_PROVIDER=gemini`
in `.env`) for development — best quality-to-cost ratio and highest context
window. Groq is wired in as an easy swap if we need faster responses for a
live demo. Both are configured in `app/core/llm_client.py`; switching providers
is a one-line `.env` change, no code changes needed.

## Project structure

```
app/
├── main.py               # FastAPI entrypoint
├── config.py              # loads .env via pydantic-settings
├── api/routes.py          # /health, /ask/cypher, /ask/graphrag, /query/raw
├── core/
│   ├── neo4j_connector.py # single shared Neo4j driver wrapper
│   └── llm_client.py       # provider-agnostic LLM getter
├── chains/
│   ├── cypher_chain.py     # LangChain GraphCypherQAChain (LLM -> Cypher -> answer)
│   └── qa_chain.py         # GraphRAG retrieval + answer chain
└── models/schemas.py       # request/response Pydantic models
```

## Git workflow

```bash
git checkout -b feature/codebase-setup
git add .
git commit -m "Set up initial project structure, Neo4j connector, and both LLM chains"
git push -u origin feature/codebase-setup
```


