import os
import asyncio
from dotenv import load_dotenv

from web3 import AsyncWeb3, WebSocketProvider

load_dotenv()

QUICK_NODE_API_KEY = os.getenv("QUICK_NODE_API_KEY")

wss_url = (
    f"wss://dawn-virulent-grass.ethereum-sepolia.quiknode.pro/{QUICK_NODE_API_KEY}"
)


async def main():
    w3: AsyncWeb3 = await AsyncWeb3(WebSocketProvider(wss_url))

    print("is_connected: ", await w3.is_connected(True))
    subscription_id = await w3.eth.subscribe("newPendingTransactions")

    counter = 0
    async for response in w3.socket.process_subscriptions():
        transaction_id = response["result"]
        transaction = await w3.eth.get_transaction(transaction_id)

        print(f"Response: {response}")
        print(f"Transaction id: {response['result']}")
        print(f"Transaction: {transaction}")

        if counter > 10:
            await w3.eth.unsubscribe(subscription_id)
            break

        counter += 1


asyncio.run(main())
