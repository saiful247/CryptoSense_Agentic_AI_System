from langgraph.graph import StateGraph
from typing import TypedDict

from app.agents.crypto_advisor_agents.coinNameToSymbolAgent import getCoinSymbol
from app.agents.crypto_advisor_agents.financeMetricAgent import get_finance_metrics
from app.agents.crypto_advisor_agents.platformSelectionAgent import get_platform_selection
from app.agents.crypto_advisor_agents.final_advice_agent import getFinalAdvice
from app.agents.crypto_advisor_agents.finalReturnAmountAgent import estimate_crypto_return_with_csv


from app.schemas.schemas import UserRequest


class GraphState(TypedDict):
    input: UserRequest
    coinSymbol: str
    finance_metrics: dict
    estimated_return_usd: dict
    platform_selection: str
    final_advice: dict


def build_graph():
    coin_symbol_fn = getCoinSymbol()
    finance_metrics_fn = get_finance_metrics()
    platform_selection_fn = get_platform_selection()
    final_advice_fn = getFinalAdvice()
    estimate_return_fn = estimate_crypto_return_with_csv()

    graph = StateGraph(GraphState)
    graph.add_node("coinSymbol", coin_symbol_fn)
    graph.add_node("finance_metrics", finance_metrics_fn)
    graph.add_node("platform_selection", platform_selection_fn)
    graph.add_node("final_advice", final_advice_fn)
    graph.add_node("estimated_return_usd", estimate_return_fn)

    graph.set_entry_point("coinSymbol")
    graph.add_edge("coinSymbol", "finance_metrics")
    graph.add_edge("finance_metrics", "estimated_return_usd")
    graph.add_edge("estimated_return_usd", "platform_selection")
    graph.add_edge("platform_selection", "final_advice")
    graph.set_finish_point("final_advice")

    return graph.compile()
