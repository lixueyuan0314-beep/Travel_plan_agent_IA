# Product case study: Human-in-the-loop travel agent

This fork extends the upstream travel agent with an explicit product safety
and preference layer. The goal is to make tool use understandable and
controllable for non-technical travellers rather than sending every parsed
request directly to live transport providers.

## User problem

Travel requests often omit constraints, and agent tool calls can be opaque.
Users need to know which route, date, providers, and preferences the agent is
about to use before it spends time or API quota on a search.

## Added product flow

1. Parse a common route request locally.
2. Display a structured preview of origin, destination, date, modes, budget,
   transfer limit, and ranking priority.
3. Wait for an explicit **Confirm and search** action.
4. Execute the existing regex fast path or LLM/MCP route.
5. Let the user cancel and adjust the request without contacting providers.

## Transparent ranking

`product/scoring.py` provides an explainable scoring model across price,
duration, transfers, and carbon emissions. Four user-selectable priorities
change the weights, while hard budget and transfer constraints filter options.
This is deliberately deterministic so a product manager can explain why one
option ranks above another.

## Offline evaluation

The product layer now has a reproducible, network-free scenario suite in
`eval/product_cases.json`. It runs without an LLM, API key, MCP server, or
transport provider and checks whether the agent should show a confirmation or
fall back for clarification.

Current result: **30/30 scenarios passed (100%)**, with **0 false
confirmations** and **0 missed confirmations**. Coverage includes:

- single-mode and multi-mode confirmation previews;
- multiword routes, relative dates, and conservative typo recovery;
- missing route parameters and ambiguous destination text;
- malformed, unrecognized, and past dates;
- invalid preference validation;
- budget and transfer constraints;
- ranking changes when the user changes priority;
- provider timeout and connection-failure recovery;
- empty-result and malformed-payload fallbacks.

Run it with:

```powershell
python -m eval.product_eval
python -m unittest tests.test_product_layer tests.test_product_eval tests.test_resilience -v
```

`product/resilience.py` normalizes untrusted provider responses into the shared
`TravelOption` schema, retries transient failures at most once, and converts
empty or malformed responses into explicit user-facing fallback states. The
key-free demo exposes these policies through an interactive fault-injection
lab. A next iteration should connect the normalized schema to every live MCP
provider and add latency and recovery-rate telemetry.

## Attribution

The transport MCP integrations, LangChain agent, regex fast path, Streamlit
UI, and LangSmith evaluation framework originate from the upstream project.
This fork's independent contribution is the confirmation, preference, ranking,
provider-recovery, security-hardening, evaluation, CI, demo, and product
documentation described above.
