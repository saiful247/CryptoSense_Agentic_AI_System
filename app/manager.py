from autogen import GroupChat, GroupChatManager
from app.agents.risk.risk_guard import create_risk_guard_agent
from app.agents.learning.learning_agent import create_learning_agent
 
 # its a virtual meeting between agents there is group chat and group chat manager
 # where it defines which agents are in the group and stores their conversation and next one
 # acts like a moderator where it decides who should speak next and when to stop

def route_initial_speaker(user_text: str) -> str: #Figures out which agent should start (RiskGuard vs LearningAgent) based on user text keywords.
    t = (user_text or "").lower()
    if any(k in t for k in ["http://","https://",".eth","token","contract","address","scam","rug","honeypot"]):
        return "RiskGuard"
    if any(k in t for k in ["explain","what is","why","how does","meaning","learn","tutorial"]):
        return "LearningAgent"
    return "RiskGuard"

def build_groupchat(): #Creates the agent instances, sets them in a GroupChat, and wraps it with a GroupChatManager.
    risk = create_risk_guard_agent("RiskGuard")
    tutor = create_learning_agent("LearningAgent")
    agents = [risk, tutor]
    gc = GroupChat(agents=agents, messages=[], max_round=4, allow_handoff=True)
    gcm = GroupChatManager(groupchat=gc, llm_config={"temperature": 0.2})
    return gc, gcm, {a.name: a for a in agents}

def run_turn(user_text: str): #Runs one full conversation round — lets the chosen agent start, then the manager lets others reply if needed.
    gc, gcm, agent_map = build_groupchat()
    first = route_initial_speaker(user_text)
    gc.messages.append({"role": "user", "content": user_text})
    reply = agent_map[first].generate_reply(messages=gc.messages)
    gc.messages.append({"role": "assistant", "name": first, "content": reply})
    final = gcm.run()
    return final

if __name__ == "__main__":
    print(run_turn("Check this URL and explain simply: https://binance-bonus-secure-login.com"))


