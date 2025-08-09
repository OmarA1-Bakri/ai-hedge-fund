# src/engine/runner.py
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.risk_manager import risk_management_agent
from src.graph.state import AgentState
from src.utils.analysts import ANALYST_ORDER, get_analyst_nodes
from src.utils.progress import progress
import json


def parse_hedge_fund_response(response: str | bytes | Any) -> Dict[str, Any] | None:
    """Parses a JSON string and returns a dictionary."""
    try:
        if isinstance(response, bytes):
            response = response.decode("utf-8")
        return json.loads(response)
    except Exception:
        # Return None on malformed content; caller prints details
        return None


def start(state: AgentState) -> AgentState:
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts: List[str] | None = None) -> StateGraph:
    """
    Build the agent workflow DAG. Accepts either internal keys or display names.
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # All available analyst nodes
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())

    # Normalize selections: accept keys or display names
    display_to_key = {display: key for display, key in ANALYST_ORDER}
    valid_keys = set(analyst_nodes.keys())
    normalized: List[str] = []
    for item in selected_analysts:
        if item in valid_keys:
            normalized.append(item)
        elif item in display_to_key and display_to_key[item] in valid_keys:
            normalized.append(display_to_key[item])
        else:
            raise KeyError(
                f"Unknown analyst selection '{item}'. "
                f"Valid keys: {sorted(valid_keys)} | "
                f"Valid displays: {sorted(display_to_key.keys())}"
            )
    # De-dup while preserving order
    seen = set()
    selected_analysts = [x for x in normalized if not (x in seen or seen.add(x))]

    # Add analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Risk & Portfolio nodes
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)
    workflow.set_entry_point("start_node")
    return workflow


def run_hedge_fund(
    tickers: List[str],
    start_date: str,
    end_date: str,
    portfolio: Dict[str, Any],
    show_reasoning: bool = False,
    selected_analysts: List[str] | None = None,
    model_name: str = "gpt-4.1",
    model_provider: str = "OpenAI",
) -> Dict[str, Any]:
    """
    Execute the agent workflow and return decisions and analyst signals.
    This is intentionally dependency-light so both CLI and backtester can call it.
    """
    progress.start()
    try:
        trading_workflow = create_workflow(selected_analysts)
        agent = trading_workflow.compile()
        final_state = agent.invoke(
            {
                "messages": [HumanMessage(content="Make trading decisions based on the provided data.")],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            }
        )
        return {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }
    finally:
        progress.stop()
