# InsureChat v3.0 — Implementation Plan

## Phase 1: Project Setup
- [x] Create folder structure
- [x] Create config.yaml, .env.example, .gitignore, requirements.txt

## Phase 2: MCP Server Tools
- [x] config_manager.py — Read/write config.yaml
- [x] embedder.py — Gemini text-embedding-004 embedding
- [x] input_validator.py — Length + injection + PII + rate limit
- [x] output_validator.py — PII mask + hallucination + confidence
- [x] vector_db.py — ChromaDB query (both collections)
- [x] ingest.py — Document extraction + chunking + embedding + ChromaDB
- [x] llm_router.py — Claude claude-sonnet-4-6 + Haiku routing
- [x] intent_classifier.py — Async Claude Haiku intent classification
- [x] analytics_logger.py — SQLite write + JSONL audit log
- [x] server.py — FastMCP server with all tools

## Phase 3: Security
- [x] security/audit_logger.py — JSONL audit log writer/reader

## Phase 4: Web Layer
- [x] fastapi_server.py — All API endpoints
- [x] streamlit_microsite.py — Insurance customer chat UI (Port 8501)
- [x] streamlit_support.py — Developer support chat UI (Port 8502)

## Phase 5: Analytics
- [x] dashboard.py — Analytics dashboard Streamlit component
- [x] reports.py — PDF + Excel report generation
- [x] anomaly_detector.py — Z-score anomaly detection

## Phase 6: Documentation & Scripts
- [x] setup.ps1 / run.ps1
- [x] README.md

## Phase 7: Verification
- [x] Install all dependencies (pip + spaCy model)
- [x] Fix type annotations for Python 3.13 / newer package versions
- [x] All 10 modules pass import + unit verification
- [x] FastAPI /health endpoint returns healthy (ChromaDB + SQLite OK)
- [x] Streamlit microsite responds on port 8501

## Review Notes
- requirements.txt uses >= constraints (not ==) due to Python 3.13 compatibility
- chromadb.PersistentClient is a factory function in v1.5.2, not a class — use Optional[Any] for type hints
- API keys (ANTHROPIC_API_KEY, GOOGLE_API_KEY) must be set in .env for full functionality
- All background processes (FastAPI, Streamlit) start and respond correctly

---

# Feature Spec: Multi-Turn Conversation Support

## Status: IMPLEMENTED (branch: feature/multi-turn-conversation)

---

## 1. Problem

InsureChat currently processes every message as a standalone query. The LLM has zero memory of prior turns. Users cannot ask follow-up questions like "What about the deductible?" after asking about auto insurance — the model won't know the topic.

## 2. Current Architecture (What Exists)

| Component | Current Behaviour |
|---|---|
| `llm_router.call_claude()` | Sends `messages=[{"role": "user", "content": ...}]` — single turn only |
| `_run_chat_pipeline()` | Stateless — no history lookup or injection |
| `ChatRequest` model | Has `session_id` but no `history` field |
| Streamlit UI | Stores `st.session_state.messages` for display only — never sent to API |
| FastAPI server | No server-side session store |
| Analytics SQLite | Logs every message with `session_id` but doesn't serve them back for context |
| `config.yaml` | No `max_history_turns` or conversation settings |

## 3. Design Goals

1. **Follow-up awareness** — The LLM sees recent conversation turns so users can reference prior messages naturally
2. **Token-budget safety** — History never exceeds a configurable cap; RAG chunks always get priority
3. **Minimal blast radius** — Changes touch 4–5 files; no schema migration needed
4. **Fallback-compatible** — Works with both Claude (native `messages` array) and Gemini (concatenated string)
5. **Security preserved** — History passes through the same PII/injection checks

## 4. Token Budget Analysis

Current per-request token consumption (approximate):

| Component | Estimated Tokens |
|---|---|
| System prompt (microsite) | ~200 |
| System prompt (support) | ~200 |
| RAG prompt template | ~50 |
| 5 chunks × ~512 tokens each | ~2,560 |
| User query (max 500 chars) | ~125 |
| **Total input (current)** | **~2,935** |
| `max_tokens` for response | 1,024 |
| **Total per request** | **~3,959** |

Claude Sonnet context window: **200,000 tokens**
Gemini 2.0 Flash context window: **1,048,576 tokens**

**Available headroom for history:** ~190,000+ tokens — but we should cap conservatively.

### Recommended budget allocation

| Component | Token Budget | Notes |
|---|---|---|
| System prompt | ~200 | Fixed |
| Conversation history | **~4,000** (configurable) | ~5–10 turns of back-and-forth |
| RAG chunks (5 × 512) | ~2,560 | Priority — always included in full |
| Current query + template | ~175 | Fixed |
| Response (`max_tokens`) | 1,024 | Fixed |
| **Total** | **~7,959** | Well within both models' limits |

## 5. Recommended Configuration

Add to `config.yaml` under a new `conversation:` section:

```yaml
# ── Conversation Memory ─────────────────────────────────────────────────────
conversation:
  max_history_turns: 5          # Max prior Q+A pairs sent to the LLM (0 = disable)
  max_history_tokens: 4000      # Hard cap on total tokens used by history
  include_sources_in_history: false  # Whether to include source citations in history turns
  storage: server               # "server" = in-memory dict; "sqlite" = persist in analytics DB
```

### Why these defaults?
- **5 turns** covers most follow-up chains (research shows 80%+ of conversations resolve within 3–5 turns)
- **4,000 tokens** safely fits 5 full exchanges without crowding out the 2,560-token RAG context
- **`include_sources_in_history: false`** — sending citations in history wastes tokens; only the answer text matters for context
- **`storage: server`** — in-memory dict is simplest for POC; graduating to SQLite is a one-line config change

## 6. Implementation Plan

### 6.1 Server-Side Session Store (new file or module addition)

**Option A: In-memory dict (POC-grade, recommended for v3.0)**
```
Dict[session_id] → List[{"role": "user"|"assistant", "content": str, "timestamp": str}]
```
- Pros: Zero dependencies, fast, simple
- Cons: Lost on server restart, unbounded memory growth without TTL
- Mitigation: Add a TTL (e.g., 30 min inactivity) and max sessions cap (e.g., 1,000)

**Option B: SQLite-backed (production-grade)**
- Reuse existing `analytics.db` with a new `conversation_history` table
- Pros: Survives restarts, queryable, already have SQLite infrastructure
- Cons: Slightly more complex, read latency (negligible for <100 rows)

**Best practice: Start with Option A, make it swappable via the `storage` config.**

### 6.2 Files to Modify

| File | Change | Complexity |
|---|---|---|
| `config.yaml` | Add `conversation:` section | Trivial |
| `mcp_server/tools/config_manager.py` | Add `get_conversation_config()` reader | Trivial |
| `mcp_server/tools/llm_router.py` | Accept `history` param; prepend to `messages` array | Medium |
| `web/fastapi_server.py` | Store/retrieve history per session in `_run_chat_pipeline` | Medium |
| `web/streamlit_support.py` | Send `session_id` (already does); no other change needed | None |
| `web/streamlit_microsite.py` | Send `session_id` (already does); no other change needed | None |

### 6.3 LLM Router Changes (core logic)

**Claude (primary)** — Native multi-turn via `messages` array:
```python
messages = []
for turn in history[-max_turns:]:
    messages.append({"role": "user", "content": turn["user"]})
    messages.append({"role": "assistant", "content": turn["assistant"]})
messages.append({"role": "user", "content": rag_prompt})  # current turn with RAG context
```

**Gemini (fallback)** — Concatenate history into the prompt string:
```python
history_text = "\n".join(
    f"User: {t['user']}\nAssistant: {t['assistant']}" for t in history[-max_turns:]
)
contents = f"{system_prompt}\n\nCONVERSATION HISTORY:\n{history_text}\n\n{rag_prompt}"
```

### 6.4 Pipeline Changes (`_run_chat_pipeline`)

```
Existing flow:          Proposed flow:
1. Input validation     1. Input validation
2. Embed query          2. Embed query
3. Retrieve chunks      3. Retrieve chunks
                        3.5 LOAD HISTORY for session_id (NEW)
4. LLM call             4. LLM call WITH HISTORY (MODIFIED)
5. Output validation    5. Output validation
6. Intent classify      6. Intent classify
7. Analytics log        7. Analytics log
                        7.5 SAVE to history store — {query, response} (NEW)
```

Only two new steps (3.5 and 7.5). Existing steps are untouched except passing `history` to the LLM router.

## 7. Best Practices & Gotchas

### 7.1 Token Counting
- **Do not guess token counts.** Use `anthropic.count_tokens()` or a tiktoken-based estimator to count history tokens before sending.
- Trim oldest turns first when history exceeds `max_history_tokens`.
- Always prioritize: RAG context > recent history > older history.

### 7.2 Security
- **Sanitize history before sending to LLM.** A prior response could contain injected content that the LLM would trust as its own.
- History should store the **sanitized query** (post-PII-redaction), not the raw user input.
- History should store the **validated output** (post-PII-masking), not the raw LLM response.
- Do NOT store blocked messages in conversation history — they add no useful context.

### 7.3 Session Isolation
- History is strictly per `session_id` — no cross-session bleeding.
- In-memory store should enforce a maximum sessions cap to prevent memory exhaustion.
- Add a TTL: clear sessions inactive for >30 minutes.

### 7.4 Prompt Engineering for Multi-Turn
- Add a line to the system prompt: `"You have access to the conversation history below. Use it to understand follow-up questions, but always ground your answers in the provided CONTEXT from the knowledge base."`
- This prevents the model from relying on history instead of RAG chunks.

### 7.5 What NOT to Do
| Anti-Pattern | Why It's Bad |
|---|---|
| Send full history every time with no cap | Token explosion; costs spike; may exceed context window |
| Store raw queries (pre-PII-redaction) in history | PII leak into LLM context on subsequent turns |
| Include RAG chunks in history turns | Wastes tokens; chunks are re-retrieved per query anyway |
| Use Streamlit session state as the history source | Streamlit state is client-side; API server can't access it |
| Skip history for the Gemini fallback path | Breaks conversation continuity when Claude is down |

### 7.6 Testing Strategy
1. **Unit test:** `call_claude()` with mock — verify history appears in `messages` array in correct order
2. **Integration test:** Send 3 sequential queries with same `session_id` — verify 3rd response references context from turn 1
3. **Token budget test:** Send a conversation with 20 turns — verify only the last `max_history_turns` are sent
4. **Security test:** Inject a prompt injection in turn 1, verify it's sanitized before being replayed in turn 2
5. **Session isolation test:** Two different `session_id` values should have independent histories

## 8. Checklist (Implementation Steps)

- [x] Add `conversation:` block to `config.yaml`
- [x] Add `get_conversation_config()` to `config_manager.py`
- [x] Create session store (in-memory dict with TTL + max cap)
- [x] Modify `call_claude()` to accept and prepend `history` parameter
- [x] Modify `_call_gemini_fallback()` to accept and prepend `history` parameter
- [x] Modify `_run_chat_pipeline()` to load history, pass to LLM, save after response
- [x] Update system prompts with history-awareness instruction
- [x] Add token counting / trimming logic
- [ ] Write unit tests for history injection and trimming
- [ ] Write integration test for multi-turn follow-ups
- [x] Update PRD and ARCHITECTURE.md to reflect the new capability
- [x] Update all Mermaid diagrams (01, 02, 03, 05, 06, 08, 11, 12)
