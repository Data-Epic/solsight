from __future__ import annotations

import asyncio
import solana
import json
from solana.rpc.async_api import AsyncClient
from solana.exceptions import SolanaRpcException
# import nest_asyncio


mainnet_url = "https://api.mainnet-beta.solana.com"


def hello(event, context):
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    return {"statusCode": 200, "body": json.dumps(body)}


async def fetch_block(url):
    try:
        async with AsyncClient(url) as client:
            latest_blockhash = await client.get_slot()
            slot = json.loads(latest_blockhash.to_json())["result"]
        return slot  # True
    except SolanaRpcException as e:
        print(e)
        return None


async def stream_data(url):
    while True:
        data = await fetch_block(url)
        if data is not None:
            # print(data)
            return data  # Process or handle the data as needed

    # await asyncio.sleep(1)


def run(event, context):
    result = asyncio.run(stream_data(mainnet_url))
    print("Data sent to firehose successfully!")
    return result


# if __name__ == "__main__":
#     run()
