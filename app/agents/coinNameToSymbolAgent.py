import re
from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()

config_list = [
    {
        "model": "gemini-2.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google"
    }
]


def getCoinSymbol():
    def get_coin_symbol_function(state):
        coinName = state["input"]["coinName"]
        print("Coin Name: ", coinName)

        instruction = f"""
        You are a crypto currency name to symbol conversion agent.
        user prompt will conatain crypto currency name {coinName}. you need to change this name to Crypto currrency symbol.
        out put only the symbol for example BTC for Bitcoin, ETH for Ethereum, LTC for Litecoin.
        output in json format like {{"coinSymbol": "BTC"}}.
        after the json output, output a single line: TERMINATE
        """

        cryptoPriceAgent = ConversableAgent(
            "cryptoPriceAgent",
            system_message=instruction,
            llm_config={
                'config_list': config_list
            },
            max_consecutive_auto_reply=2,
            human_input_mode="NEVER",
        )

        user_proxy = ConversableAgent(
            "user_proxy",
            llm_config=False,
            human_input_mode="NEVER",
            is_termination_msg=lambda msg: msg.get(
                # if the message(reply) from CryptoPriceAgent contains TERMINATE, then stop
                "content") is not None and "TERMINATE" in msg["content"],
        )

        prompt = coinName

        result = user_proxy.initiate_chat(
            cryptoPriceAgent, message=prompt)

        print("result: ", result)
        final_text = result.chat_history[1].get("content", "")
        print("Final Result in coin name to symbol agent: ", final_text)

        try:
            final_text = re.sub(r"^```json\s*", "", final_text)
            final_text = re.sub(r"\s*```\s*", "", final_text)
            final_text = re.sub(r"\s*TERMINATE\s*$", "", final_text)
            print("After cleaning: ", final_text)
            final_result = final_text
            try:
                print("Final Result XX str: ", final_result)
                final_dict = json.loads(final_result)
                print("Final Result XX dict: ", final_dict)
                coinSymbol = final_dict.get("coinSymbol", "")
                print("Coin Symbol: ", coinSymbol)

                state["coinSymbol"] = coinSymbol

            except Exception as e:
                print("Error in parsing to pydantic model: ", str(e))
                state["coinSymbol"] = ""

        except Exception as e:
            state["coinSymbol"] = ""
            print("Error in processing final result: ", str(e))

        return state
    return get_coin_symbol_function
