---

# fetchSimilarQueries RAG Tool + Neo4j Grounding Pipeline

Following the initial Neo4j tool integration (see above), the next requirement was to implement a second tool, `fetchSimilarQueries`, backed by a FAISS RAG index over 30 example question/Cypher pairs. During testing, several issues were found in the tool-calling sequence and answer-grounding behavior — these are documented below along with the fixes applied.

## Objective

Implement `fetchSimilarQueries` as a RAG tool that retrieves similar Cypher examples to guide query generation, while ensuring:
- The LLM writes its own short natural-language search phrase (not the full user question)
- Neo4j remains the only source of truth for the final answer
- FAISS/RAG output is never used as medical evidence

## Implementation

* Built a FAISS index (`sentence-transformers/all-MiniLM-L6-v2`) over 30 stored question/Cypher examples from an Excel databank.
* Registered `fetchSimilarQueries` as a second Groq tool alongside `execute_neo4j_query`.
* Restructured the single-completion tool-calling flow into a 3-stage forced sequence: RAG retrieval → Cypher generation (informed by retrieved examples) → Neo4j execution → grounded final answer.
* Replaced keyword-based routing (`should_use_neo4j_tool`) with an LLM classifier call to reliably detect biomedical questions.
* Added error handling around all Groq calls to prevent malformed tool calls from crashing the endpoint.

---

## Issues Found During Testing

### 1. FAISS answer leakage
The RAG index initially returned a `finding` field alongside `question` and `cypher`. The LLM sometimes echoed this stored text directly as its final answer instead of querying Neo4j.

**Fix:** Removed `finding` from `fetch_similar_queries()`'s return value in `rag_tool.py`.
 
### Before fix
![finding leak before fix](images/rag_leak_before.png)
### After fix
![finding removed after fix](images/rag_leak_fixed.png)

### 2. Second tool never called
With `tool_choice="auto"`, the model sometimes stopped after calling `fetchSimilarQueries` and never called `execute_neo4j_query` — meaning the final answer was built without ever touching Neo4j.

**Fix:** Split the single completion into three forced-tool-choice completions, guaranteeing both tools fire in the correct order every time.

### Before fix
![sequential tool calls in log](images/staged_tool_calls.png)

### 3. Routing missed real medical questions
A fixed keyword list (`medical_keywords = [...]`) failed to route questions like drug-name-based queries ("ibuprofen and warfarin") or unlisted conditions ("psoriasis lifestyle changes") to the Neo4j pipeline — these fell through to a no-tools branch, in one case producing a fabricated answer falsely attributed to Neo4j.

**Fix:** Replaced the keyword list with an LLM-based classifier call.

### Before fix
![misrouted question before fix](images/router_before.png)
### After fix
![correct routing after fix](images/router_after.png)

### 4. Fabricated advice layered on real graph facts
For questions asking "what lifestyle changes can help," the model correctly listed real exposure-disease associations from Neo4j, but then invented remediation advice (e.g., "use a HEPA vacuum") not present in the graph.

**Fix:** Added explicit before/after examples to the final-answer system prompt distinguishing "reporting an association" from "inventing guidance."

### Before fix
![fabricated advice before fix](images/advice_leak_before.png)
### After fix
![grounded-only answer after fix](images/advice_leak_fixed.png)

---

## Verification

Test queries covering multiple relationship types in PrimeKG:

```text
I've been diagnosed with psoriasis. Are there other diseases that commonly occur with it?
My father has type 2 diabetes, what other conditions is he at risk for?
What genes are associated with asthma?
Can I take ibuprofen and warfarin together?
What environmental factors should I avoid to prevent asthma?
```

Result:

* `fetchSimilarQueries` correctly invoked first, with a short LLM-generated search phrase (not the full user question).
* Retrieved examples correctly informed Cypher generation for each relationship type (disease-disease, disease-gene, disease-drug, drug-drug, exposure-disease).
* `execute_neo4j_query` reliably invoked second, using the generated Cypher.
* Final answers grounded strictly in Neo4j results, with explicit "not available in the knowledge graph" fallback when queries returned empty.

### End-to-end successful run
![end-to-end successful run](images/pipeline_success.png)

### OpenWebUI  final answer
![OpenWebUI rendered final answer](images/openwebui_result.png)

---

