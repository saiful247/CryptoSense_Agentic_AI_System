

# app/agents/history_agent.py
from typing import Dict, Any, List
from app.db.history_store import HistoryStore

_store = HistoryStore()

def history_log(result: Dict[str, Any]) -> None:
    item = {
        "kind": result.get("kind"),
        "input": result.get("url") or result.get("symbol") or result.get("address") or "",
        "risk": result.get("risk"),
        "score": int(result.get("score", 0)),
        "reasons": result.get("reasons") or [],
    }
    # Avoid logging empty items (e.g., if everything missing)
    if item["kind"] and item["input"]:
        _store.add_record(item)

def history_nearest_probe(kind: str, value: str, reasons: List[str]) -> List[Dict[str, Any]]:
    parts = [kind or "", value or "", " ; ".join(reasons or [])]
    query = " | ".join([p for p in parts if p])
    if not query.strip():
        return []
    return _store.similar(query_text=query, top_k=5)
