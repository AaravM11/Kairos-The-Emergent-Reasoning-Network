# Kairos — The Emergent Reasoning Network

**Multi-agent reasoning marketplace: KG-grounded answers, validator scores, winner & IPFS snapshots.**

Kairos runs several reasoning modules (audit, macro, sentiment, DeFi risk, and extensible agents) on the **same question** and a shared **knowledge graph**. Each answer is scored by **validation nodes**—grounding against the graph, plus logical consistency, novelty, and alignment when an LLM is configured. The orchestrator ranks modules, picks a **winner**, and **pins** graph snapshots, round payloads, and per-agent memory to **IPFS** (content-addressed CIDs).

The stack pairs a **Next.js** UI and API routes with a **Python** orchestrator (`scripts/run_marketplace_round.py`, `core/orchestrator`). The main demo flow is: ingest or refresh `output/knowledge_graph.json` → **Run marketplace round** from the UI (`POST /api/query`) → inspect the leaderboard, winner validation, and CIDs on an IPFS gateway.

## Prerequisites

- **Node.js** 18+ (for `npm run dev` / `next build`)
- **Python** 3.11+ with `pip install -r requirements-runtime.txt` (marketplace + validators; full stack also has `requirements.txt`)
- **IPFS** daemon on `127.0.0.1:5001` if you want real uploads (or set `KAIROS_FAKE_IPFS=1` for local/tests)
- **OpenAI** and/or **Ollama**: logical, novelty, and alignment validators need an LLM. Grounding does not.

## Environment

Copy secrets locally (never commit `.env`). Common variables:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI path for validators and OpenAI-backed modules |
| `OPENAI_MODEL` | e.g. `gpt-4o-mini` (see `core/openai_model.py`) |
| `LLM_PROVIDER` | `openai` (default) or `ollama` |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | When using Ollama |
| `KAIROS_PYTHON` | Path to venv Python for `/api/query` (e.g. `.venv/bin/python`) |
| `KAIROS_FAKE_IPFS` | `1` = deterministic fake CIDs (tests / no daemon) |
| `AGENT_MEMORY_REGISTRY_PATH` | Optional override for agent memory registry file |

## Quick start

```bash
npm install
pip install -r requirements-runtime.txt

# Optional: point Next at your venv interpreter
export KAIROS_PYTHON="$(pwd)/.venv/bin/python"

# Optional: IPFS (or export KAIROS_FAKE_IPFS=1)
ipfs daemon   # separate terminal

npm run dev
```

Open [http://localhost:3000](http://localhost:3000), upload a PDF via **Upload PDF** if your ingest pipeline is wired, then run a **marketplace round** with a natural-language question.

## CLI and tests

```bash
# One-off round from the shell (stdin JSON)
echo '{"query":"What risks matter for TokenX?"}' | python scripts/run_marketplace_round.py

python scripts/kairos_cli.py --help

python tests/integration_test.py
```

## Leaderboard scoring

Validator metrics include **logical consistency**, **grounding**, **novelty**, and **alignment** (each 0–1 when run). The UI **Score** blends **72%** of the average of those four with **28%** of each module’s self-reported **confidence**, so modules do not tie when LLM validators are skipped or identical. See `core/orchestrator/index.py` for details.

## Repository layout (high level)

| Path | Role |
|------|------|
| `core/orchestrator/` | Marketplace loop, validation, memory, IPFS hooks |
| `core/knowledge_graph/` | Graph load/query (Python) |
| `core/llm_client.py` | OpenAI vs Ollama chat completion |
| `core/storage/ipfs.py` | IPFS upload / optional backends |
| `reasoning_modules/` | Agent implementations |
| `validation_nodes/` | Grounding + LLM validators |
| `pages/api/query.ts` | Spawns Python marketplace runner |
| `frontend/KairosApp.tsx` | Main UI |
| `output/knowledge_graph.json` | Default graph path for rounds |
| `scripts/` | CLI, `run_marketplace_round.py` |

## License / credits

See repository metadata and upstream contributors (e.g. FranklinDAO / hackathon lineage). Ensure API keys and registry files stay out of version control.
