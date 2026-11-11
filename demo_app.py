"""Key-free Streamlit portfolio demo for the travel-agent product layer."""
from __future__ import annotations

import streamlit as st

from MCP.skills import parse_query
from product.confirmation import UserPreferences, build_search_plan
from product.demo_data import generate_demo_options
from product.scoring import WEIGHTS, rank_options


st.set_page_config(page_title="Travel Agent Product Demo", page_icon="🧭", layout="centered")

st.title("🧭 Travel Agent Product Demo")
st.caption(
    "A key-free portfolio demo of the recommend → confirm → execute flow. "
    "Options and prices are simulated; no provider or LLM is contacted."
)

with st.sidebar:
    st.header("Trip preferences")
    priority = st.selectbox(
        "Ranking priority",
        ["balanced", "cheapest", "fastest", "fewest_changes"],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    use_budget = st.checkbox("Set a maximum budget")
    budget = st.number_input("Maximum budget (EUR)", min_value=1, value=150, disabled=not use_budget)
    limit_changes = st.checkbox("Limit transfers")
    changes = st.number_input("Maximum changes", min_value=0, value=1, disabled=not limit_changes)
    st.divider()
    st.info("Try: **Plan a trip from Paris to Lyon tomorrow**")

preferences = UserPreferences(
    priority=priority,
    max_budget_eur=float(budget) if use_budget else None,
    max_changes=int(changes) if limit_changes else None,
)

if "demo_plan" not in st.session_state:
    st.session_state.demo_plan = None
if "demo_results" not in st.session_state:
    st.session_state.demo_results = None

query = st.text_input(
    "Where would you like to go?",
    value="Plan a trip from Paris to Lyon tomorrow",
)

if st.button("Build recommendation", type="primary"):
    parsed = parse_query(query)
    st.session_state.demo_results = None
    if parsed is None:
        st.session_state.demo_plan = None
        st.warning(
            "I need a clear origin, destination, and valid date before I can prepare a search. "
            "Try: “Train from Paris to Bordeaux on 2099-06-10”."
        )
    else:
        st.session_state.demo_plan = build_search_plan(query, parsed, preferences)

plan = st.session_state.demo_plan
if plan is not None:
    st.info(plan.to_markdown())
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Confirm simulated search", type="primary", use_container_width=True):
        st.session_state.demo_results = rank_options(generate_demo_options(plan), plan.preferences)
    if cancel_col.button("Cancel", use_container_width=True):
        st.session_state.demo_plan = None
        st.session_state.demo_results = None
        st.rerun()

ranked = st.session_state.demo_results
if ranked:
    st.subheader("Ranked options")
    rows = []
    for option, score in ranked:
        rows.append(
            {
                "Option": option.label,
                "Price (EUR)": option.price_eur,
                "Duration": f"{option.duration_minutes // 60}h {option.duration_minutes % 60:02d}m",
                "Changes": option.changes,
                "CO₂ (kg)": option.carbon_kg,
                "Score": score,
                "Status": "Filtered by constraints" if score == 0 else "Eligible",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    weights = WEIGHTS[plan.preferences.priority]
    with st.expander("Why did these options rank this way?"):
        st.write(
            "Scores are deterministic and combine price, duration, changes, and carbon. "
            f"For **{plan.preferences.priority.replace('_', ' ')}**, the weights are "
            f"**{weights[0]:.0%} / {weights[1]:.0%} / {weights[2]:.0%} / {weights[3]:.0%}**. "
            "Options outside hard budget or transfer limits receive a score of zero."
        )
        st.caption("Portfolio simulation only — not live availability or booking advice.")

st.divider()
st.caption("Built as an independent product extension of the upstream MCP travel-agent project.")
