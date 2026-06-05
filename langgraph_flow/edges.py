from .state import CandidateState
from config import settings, get_client


def edge_after_duplicate_check(state: CandidateState) -> str:
    if state.get("decision") == "duplicate":
        return "handle_duplicate"
    if state.get("error"):
        return "handle_error"
    return "prescreening"


def edge_after_prescreening(state: CandidateState) -> str:
    if state.get("error"):
        return "handle_error"
    retries = state.get("completeness_retries", 0)
    max_retries = settings.max_completeness_retries
    if state.get("incompleto") and retries < max_retries:
        return "ask_missing_info"
    return "rag_evaluation"


def edge_after_scoring(state: CandidateState) -> str:
    if state.get("error"):
        return "handle_error"
    return "selfcorrection"


def edge_decision(state: CandidateState) -> str:
    if state.get("error"):
        return "handle_error"
    client_config = get_client(state.get("client_id", "demo"))
    threshold = client_config.get("score_threshold") or settings.score_threshold
    score_final = state.get("score_final", 0)
    if score_final >= threshold:
        return "notify_recruiter"
    return "talent_bank"