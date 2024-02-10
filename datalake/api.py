from __future__ import annotations

import asyncio
import solana
import json
from solana.rpc.async_api import AsyncClient
from solana.exceptions import SolanaRpcException
import boto3
import logging

logging.basicConfig(level=logging.INFO)

mainnet_url = "https://api.mainnet-beta.solana.com"
client = boto3.client("firehose", endpoint_url="http://localhost:4566")


async def fetch_block(url):
    try:
        async with AsyncClient(url) as client:
            latest_blockhash = await client.get_slot()
            slot = json.loads(latest_blockhash.to_json())["result"]
        return slot  # True
    except SolanaRpcException as e:
        logging(e)
        return None


async def stream_data(url):
    while True:
        data = await fetch_block(url)
        if data is not None:
            return data  # Process or handle the data as needed

    # await asyncio.sleep(1)


def run(event, context):
    result = asyncio.run(stream_data(mainnet_url))
    x = client.put_record(Record={"Data": json.dumps(
        result)}, DeliveryStreamName="local-serverless-kinesis-firehose")
    logging("Data sent to firehose successfully!")
    return x
