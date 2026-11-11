# Agent-IA-Apprentissage

[![Product safety evaluation](https://github.com/lixueyuan0314-beep/Travel_plan_agent_IA/actions/workflows/product-eval.yml/badge.svg)](https://github.com/lixueyuan0314-beep/Travel_plan_agent_IA/actions/workflows/product-eval.yml)

**Live portfolio demo:** [lixueyuan-travel-agent-demo.streamlit.app](https://lixueyuan-travel-agent-demo.streamlit.app/)

> Un projet pour approfondir mes connaissances en LLM, Agent IA, RAG, MCP…

## Fork extension: product safety and preference controls

This fork adds a human-in-the-loop product layer on top of the upstream travel
agent:

- structured **recommend → confirm → execute** flow before live MCP searches;
- user-controlled budget, transfer limit, and ranking priority;
- transparent option-scoring utilities with deterministic tests;
- a reproducible 30-case offline safety and recovery evaluation with no API keys required;
- bounded retry, payload validation, and user-safe fallbacks for provider failures;
- safer diagnostics that never display API-key prefixes;
- a documented product case study in [PRODUCT_CASE_STUDY.md](PRODUCT_CASE_STUDY.md).

The original MCP integrations, agent routing, UI, and evaluation framework are
credited to the upstream project. The items above are the fork's independent
extension.

| Upstream foundation | Independent contribution in this fork |
| --- | --- |
| Transport MCP integrations and LangChain routing | Human-in-the-loop authorization and preference controls |
| Regex fast path and original full-agent UI | Key-free product demo and transparent ranking |
| Original LangSmith evaluation framework | 30-case offline safety/recovery suite and GitHub Actions CI |
| Provider tool calls | Payload normalization, bounded retry, and user-safe fallbacks |

### Reproduce the product evaluation

```powershell
python -m eval.product_eval
python -m unittest tests.test_product_layer tests.test_product_eval tests.test_resilience -v
```

Current result: **30/30 offline scenarios passed (100%)**, with **0 false
confirmations** and **0 missed confirmations**. The scenarios cover valid
single- and multi-mode routes, missing fields, ambiguous destination text,
invalid or past dates, typo recovery, preference validation, provider timeouts,
connection failures, empty results, and malformed payloads. They never contact
an LLM, MCP server, or transport provider.

### Run the key-free portfolio demo

```powershell
streamlit run demo_app.py
```

The demo uses clearly labelled, deterministic sample options so reviewers can
experience confirmation, hard constraints, explainable ranking, and an
interactive provider-failure lab without adding API keys or contacting live
providers. Use `app.py` for the full MCP agent with configured credentials.

A French-Europe **travel CLI/web agent**: real-time flights (Duffel),
trains (SNCF Open Data), and buses (FlixBus) wired into a LangChain
agent with three transport MCP servers, a regex fast-path that
bypasses the LLM for common shapes (~5× speedup), an on-demand skill
markdown for complex reasoning, a Streamlit chat UI, and a LangSmith
eval suite.

## Quick start

```powershell
# install
cd "Agent-IA-Apprentissage"
py -m pip install -r requirements-langchain.txt
cd MCP\flights-mcp  ; py -m uv sync ; cd ..\..
cd MCP\flixbus-mcp  ; py -m uv sync ; cd ..\..

# configure
copy .env.example .env       # then edit .env with your API keys

# run (any one)
py ask.py "TGV from Paris to Bordeaux on 2026-05-25"     # one-shot CLI
py chat.py                                                # multi-turn REPL
py -m streamlit run app.py                                # browser UI
```

## Full documentation

See **[USAGE.md](USAGE.md)** for:
- Detailed architecture diagram
- Configuration reference (all env vars)
- Evaluation suite (`eval/langsmith_eval.py`)
- Known issues + troubleshooting
- How to add new MCPs / skills

## What it looks like

```
you> Plan a trip from Paris to Lyon on 2026-05-25

[skill: plan]  Paris → Lyon on 2026-05-25
### ✈ Flights
    EUR44.01  CDG→LYS  14:42 → 15:49  (1h07m)  Iberia  [Non-stop]
    EUR44.69  CDG→LYS  14:42 → 15:49  (1h07m)  British Airways  [Non-stop]
    ...
### 🚆 Trains
  🚆 TGV INOUI  06:20 → 08:34  2h14m  (direct)
  🚆 TGV INOUI  07:00 → 09:10  2h10m  (direct)
  ...
### 🚌 Buses
  Direct FlixBus options ...

[skill answered in 4.5s — no LLM used]
```

Three modes fired in parallel through the regex fast-path,
no LLM round-trip. For free-text queries the LLM takes over with the
travel skill loaded on demand.

## License

Our code: MIT. Vendor MCPs under `MCP/flights-mcp/` and `MCP/flixbus-mcp/`
retain their upstream licenses.
