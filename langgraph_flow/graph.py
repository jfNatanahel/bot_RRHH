from langgraph.graph import StateGraph, END

from .state import CandidateState
from .nodes import (
    node_ingest_cv,
    node_check_duplicate,
    node_prescreening,
    node_ask_missing_info,
    node_rag_evaluation,
    node_scoring,
    node_selfcorrection,
    node_notify_recruiter,
    node_talent_bank,
    node_handle_duplicate,
    node_handle_error,
)
from .edges import (
    edge_after_duplicate_check,
    edge_after_prescreening,
    edge_after_scoring,
    edge_decision,
)


def build_graph():
    graph = StateGraph(CandidateState)

    graph.add_node("ingest_cv", node_ingest_cv)
    graph.add_node("check_duplicate", node_check_duplicate)
    graph.add_node("prescreening", node_prescreening)
    graph.add_node("ask_missing_info", node_ask_missing_info)
    graph.add_node("rag_evaluation", node_rag_evaluation)
    graph.add_node("scoring", node_scoring)
    graph.add_node("selfcorrection", node_selfcorrection)
    graph.add_node("notify_recruiter", node_notify_recruiter)
    graph.add_node("talent_bank", node_talent_bank)
    graph.add_node("handle_duplicate", node_handle_duplicate)
    graph.add_node("handle_error", node_handle_error)

    graph.set_entry_point("ingest_cv")
    graph.add_edge("ingest_cv", "check_duplicate")
    graph.add_edge("ask_missing_info", "prescreening")
    graph.add_edge("rag_evaluation", "scoring")
    graph.add_edge("notify_recruiter", END)
    graph.add_edge("talent_bank", END)
    graph.add_edge("handle_duplicate", END)
    graph.add_edge("handle_error", END)

    graph.add_conditional_edges(
        "check_duplicate",
        edge_after_duplicate_check,
        {
            "handle_duplicate": "handle_duplicate",
            "handle_error": "handle_error",
            "prescreening": "prescreening",
        },
    )

    graph.add_conditional_edges(
        "prescreening",
        edge_after_prescreening,
        {
            "handle_error": "handle_error",
            "ask_missing_info": "ask_missing_info",
            "rag_evaluation": "rag_evaluation",
        },
    )

    graph.add_conditional_edges(
        "scoring",
        edge_after_scoring,
        {
            "handle_error": "handle_error",
            "selfcorrection": "selfcorrection",
        },
    )

    graph.add_conditional_edges(
        "selfcorrection",
        edge_decision,
        {
            "handle_error": "handle_error",
            "notify_recruiter": "notify_recruiter",
            "talent_bank": "talent_bank",
        },
    )

    return graph.compile()


compiled_graph = build_graph()