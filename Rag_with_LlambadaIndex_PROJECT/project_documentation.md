# Project Documentation

## Architectural Decisions
- Migrated engine architecture to an Event-Driven workflow in [workflow_engine.py](workflow_engine.py).
- Steps are explicit and typed by events: ingest -> validate_query -> route_search -> run_search -> handle_retry/handle_failure -> format_result.
- Runtime services (Gemini, Cohere, Pinecone) are initialized lazily to avoid process crash at import/startup.
- Workflow state is minimal and local to the workflow instance; routing decisions are carried via events.
- Stage C architecture added: a structured data layer is generated from markdown docs via [prepare.py](prepare.py) and queried for list/time/recency questions.
- Router decision now happens inside workflow using query heuristics to choose between `structured` and `semantic` paths.

## UI/UX Design
- Not applicable for this backend refactor stage.
- No frontend visual changes were made in this phase.

## Technical Specs
- Stack: Python, LlamaIndex Workflow, Pinecone Vector Store, Cohere embeddings, Gemini LLM, Gradio UI.
- Added input validations: empty query, too-short query, repeated-character noisy input.
- Added retrieval validations: empty answer, no source nodes, retry path with expanded query and higher top-k.
- Added graceful failure handling for SSL/network/provider failures to return a user-facing message instead of crashing.
- Moved secrets out of source code and into environment variables: COHERE_API_KEY, GEMINI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_NAMESPACE.
- Known limitation: current environment still has SSL handshake failures with Gemini in this network, but the app now starts and fails gracefully at query time.
- Added runtime fallback switch: `ALLOW_OFFLINE_FALLBACK=1` enables retrieval-only answers when Gemini is blocked.
- Output now reports execution mode (`LLM מלא` or `Fallback אחזור`) and confidence indicators.
- Implemented Structured Data Extraction pipeline in [prepare.py](prepare.py) that creates [structured_data.json](structured_data.json) with schema:
	- `decisions`
	- `rules`
	- `warnings`
	- `env_vars`
	- `changes`
- Added source provenance per item (file + line range + observed time) and root source metadata (hash + mtime).
- Added structured query helpers (`route_query_mode`, `query_structured_data`) and integrated them in [workflow_engine.py](workflow_engine.py).
- Routing behavior:
	- Structured path for list/recency/time-sensitive questions.
	- Semantic path for open Q&A (with existing online/offline fallback behavior).

## Changelog
- 2026-07-15: Rewrote [workflow_engine.py](workflow_engine.py) to Event-Driven architecture with explicit event routing.
- 2026-07-15: Added validation and retry logic for low-quality or missing retrieval results.
- 2026-07-15: Implemented lazy runtime initialization and graceful error handling for external provider failures.
- 2026-07-15: Re-created root documentation file [project_documentation.md](project_documentation.md) to preserve project knowledge tracking.
- 2026-07-15: Added offline fallback mode for SSL-blocked environments so Gradio remains usable and returns retrieval-based answers.
- 2026-07-15: Added deployment/run instructions and troubleshooting guide in [README.md](README.md).
- 2026-07-15: Refactored [prepare.py](prepare.py) into reusable structured extraction and query utilities.
- 2026-07-15: Generated [structured_data.json](structured_data.json) from markdown sources.
- 2026-07-15: Integrated Stage C routing into [workflow_engine.py](workflow_engine.py) with explicit `structured` vs `semantic` path selection.
