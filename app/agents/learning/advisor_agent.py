# app/agents/advisor_agent.py
from typing import Dict, Any, List
from autogen import ConversableAgent
from app.agents.risk.common import AUTOGEN_CONFIG_LIST, clamp

#The AdvisorAgent reads all the findings produced by other agents
#(RiskGuard, Blockchain, History, ThreatIntel)
#and produces clear, human-friendly safety recommendations —
#basically: “what should the user do next?”

def _pull_reasons(*chunks: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for ch in chunks:
        if not ch:
            continue
        out.extend(ch.get("reasons") or [])
    return out[:8]


def advise_next_steps(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: combined bundle from all agents (riskguard, blockchain, history, threatintel)
    Output: JSON with summarized markdown advice.
    """
    rg = result.get("riskguard") or {}
    bc = result.get("blockchain") or {}
    hi = result.get("history") or {}
    ti = result.get("threatintel") or {}

    scores = [
        s for s in [rg.get("score"), bc.get("score"), hi.get("score"), ti.get("score")]
        if isinstance(s, (int, float))
    ]
    overall = max(scores) if scores else (rg.get("score") or 0)
    level = "low" if overall < 30 else ("medium" if overall < 60 else "high")

    bullets = []

    # Threat intel flags
    if any("known scam" in (r.lower()) for r in (ti.get("reasons") or [])):
        bullets.append("⚠️ Listed on threat-intel feeds (known scam). Avoid interacting.")

    # Blockchain flags
    if any("mintable" in (r.lower()) or "blacklist" in (r.lower()) for r in (bc.get("reasons") or [])):
        bullets.append("🔒 Contract has admin privileges (mint/blacklist). Treat as high risk.")

    # URL or token-level guidance
    if rg.get("kind") == "url":
        if level == "high":
            bullets.append("❌ Do **not** click or connect a wallet to this site.")
        else:
            bullets.append("🧭 Proceed only from verified official URLs.")
    if rg.get("kind") in ("token", "contract") or bc:
        if level == "high":
            bullets.append("❌ Do not buy / approve / sign. Exit exposure immediately.")
        else:
            bullets.append("🧪 Start with tiny exposure after verifying contract & liquidity lock.")

    # Universal safe practices
    bullets.append("🧰 Never enter seed phrase or private keys — no legit app will ask.")

    md = []
    md.append(f"### Advisor: What to do next\n")
    md.append(f"**Overall risk:** **{level.upper()}** (approx. {int(overall)}/100)\n")
    md.append("**Reasons (top):**")
    for r in _pull_reasons(rg, bc, hi, ti)[:5]:
        md.append(f"- {r}")
    md.append("\n**Recommended actions:**")
    for b in bullets:
        md.append(f"- {b}")
    md.append("\n**Optional deeper checks:**")
    md.append("- Compare with official contract address from verified sources (CoinGecko, project site).")
    md.append("- Re-run on another chain explorer (Etherscan, Snowtrace, BscScan).")
    md.append("- Check project reputation on GitHub or Twitter before any interaction.")

    return {
        "kind": "advice",
        "risk_level": level,
        "score": int(overall),
        "actions_md": "\n".join(md),
    }


def create_advisor_agent(name: str = "AdvisorAgent") -> ConversableAgent:
    system_prompt = """
    You are the AdvisorAgent — a crypto safety assistant.
    Your job is to interpret results from RiskGuard, BlockchainAgent, HistoryAgent, and ThreatIntelAgent,
    and generate **clear, human-friendly next-step safety recommendations**.

    Always:
    - Use markdown bullet points.
    - Emphasize security, verification, and caution.
    - NEVER provide financial or investment advice.
    - NEVER request personal data, wallet details, or seed phrases.

    If risk is high → focus on stopping actions, reporting, and isolation.
    If risk is medium → suggest verifying sources, contracts, and research.
    If risk is low → remind users to stay informed, diversify, and use secure wallets.

    You can use the 'advise_next_steps' tool to summarize multi-agent results.
    """

    agent = ConversableAgent(
        name=name,
        system_message=system_prompt,
        llm_config={"config_list": AUTOGEN_CONFIG_LIST, "temperature": 0.2},
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    agent.register_function({"advise_next_steps": advise_next_steps})
    return agent
