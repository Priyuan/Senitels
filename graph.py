from langgraph.graph import StateGraph, END
from state import GraphState
from agents import agent_investigator, agent_archivist

def run_investigator(state: GraphState) -> GraphState:
    """Node for Agent Alpha."""
    report = agent_investigator(state["original_claim"])
    return {
        **state,
        "verification_report": report,
        "human_review_needed": False,
        "error_message": None,
    }

def run_archivist(state: GraphState) -> GraphState:
    """Node for Agent Beta."""
    report = state["verification_report"]
    action = agent_archivist(report)
    return {
        **state,
        "db_action": action,
        "human_review_needed": (action == "FLAG"),
    }

def should_continue(state: GraphState) -> str:
    """Route to END after Archivist completes."""
    return END

# Build the graph
builder = StateGraph(GraphState)
builder.add_node("investigator", run_investigator)
builder.add_node("archivist", run_archivist)

builder.set_entry_point("investigator")
builder.add_edge("investigator", "archivist")
builder.add_conditional_edges("archivist", should_continue)

graph = builder.compile()