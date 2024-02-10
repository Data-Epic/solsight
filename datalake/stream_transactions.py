from __future__ import annotations

import asyncio
import solana
import json
from solana.rpc.async_api import AsyncClient
from solana.exceptions import SolanaRpcException, SolanaExceptionBase
import boto3
import logging

logging.basicConfig(level=logging.INFO)


mainnet_url = "https://api.mainnet-beta.solana.com"
client = boto3.client("firehose", endpoint_url="http://localhost:4566")


def check_transaction_program(transaction) -> bool:
    """
    Verify that the first and last transaction programs are spl-token
    :param transaction: The transaction to be checked
    :return: True if the programs are 'spl-token', False otherwise
    """
    first_transaction_program = None
    last_transaction_program = None

    try:
        if "program" in transaction["meta"]["innerInstructions"][0]["instructions"][0].keys():
            first_transaction_program = transaction["meta"]["innerInstructions"][0]["instructions"][0]["program"]
            last_transaction_program = transaction["meta"]["innerInstructions"][0]["instructions"][-1]["program"]
        elif "program" in transaction["meta"]["innerInstructions"][0]["instructions"][1].keys():
            first_transaction_program = transaction["meta"]["innerInstructions"][0]["instructions"][1]["program"]
            last_transaction_program = transaction["meta"]["innerInstructions"][0]["instructions"][-1]["program"]
    except:
        pass

    if first_transaction_program != "spl-token":
        return False

    if last_transaction_program != "spl-token":
        return False

    return True


def check_transaction_type(transaction) -> bool:
    """
    Verify that the first and last transaction types are transfer
    :param transaction: The transaction to be checked
    :return: True if the types are 'transfer', False otherwise
    """
    try:
        if "parsed" in transaction["meta"]["innerInstructions"][0]["instructions"][0].keys():
            first_transaction_type = transaction["meta"]["innerInstructions"][0]["instructions"][0]["parsed"]["type"]
            second_transaction_type = transaction["meta"]["innerInstructions"][0]["instructions"][-1]["parsed"]["type"]
        elif "parsed" in transaction["meta"]["innerInstructions"][0]["instructions"][1].keys():
            first_transaction_type = transaction["meta"]["innerInstructions"][0]["instructions"][1]["parsed"]["type"]
            second_transaction_type = transaction["meta"]["innerInstructions"][0]["instructions"][-1]["parsed"]["type"]
    except:
        first_transaction_type = None
        second_transaction_type = None

    if first_transaction_type != "transfer":
        return False

    if second_transaction_type != "transfer":
        return False
    return True


def check_token_address(transaction) -> bool:
    """
    Verify that the token address source is USDC and the token address destination is wrapped solana
    :param transaction: The transaction to be checked
    :return: True if the token addresses are as expected, False otherwise
    """
    usdc_token_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    wrapped_btc = "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E"
    wrapped_solana = "So11111111111111111111111111111111111111112"

    token_address_source = None
    token_address_destination = None

    try:
        token_address_source = transaction["meta"]["preTokenBalances"][0]["mint"]
        token_address_destination = transaction["meta"]["preTokenBalances"][-1]["mint"]
    except:
        pass

    if token_address_source not in [usdc_token_address, wrapped_btc]:
        return False

    if token_address_destination != wrapped_solana:
        return False

    return True


def check_error_status(transaction) -> bool:
    """
    Verify that the error and status are None
    :param transaction: The transaction to be checked
    :return: True if both error and status are None, False otherwise
    """
    error, status = "", ""
    try:
        error = transaction["meta"]["err"]
        status = transaction["meta"]["status"]["Ok"]
    except:
        pass

    if (error is None) and (status is None):
        return True

    return False


async def fetch_block(url):
    """
    Asynchronously fetches the latest block from a given URL and extracts the slot information.

    :param url: The URL of the blockchain API.
    :return: The slot of the latest block.
    """
    async with AsyncClient(url) as client:
        latest_blockhash = await client.get_latest_blockhash()
        slot = json.loads((latest_blockhash).to_json())[
            "result"]["context"]["slot"]
    # True (this comment seems to be a placeholder, you may want to review or replace it)
    return slot


async def stream_data(url):
    """
    Asynchronously streams data by repeatedly fetching the latest block from a given URL.

    :param url: The URL of the blockchain API.
    :return: The fetched data (slot of the latest block).
    """
    while True:
        data = await fetch_block(url)
        if data is not None:
            return data  # Process or handle the data as needed

        await asyncio.sleep(1)


def retrieve_transaction_details(transaction):
    """
    Retrieves details from a transaction if it meets certain criteria.

    Criteria:
    - Token address, transaction program, transaction type, and error status are verified.
    - Inner instructions and parsed information are checked.
    - If criteria are met, relevant details are extracted from the transaction.

    :param transaction: The transaction to retrieve details from.
    :return: A dictionary containing relevant transaction details if criteria are met, otherwise None.
    """
    if check_token_address(transaction) and check_transaction_program(transaction) and check_transaction_type(transaction) and check_error_status(transaction):
        if len(transaction["meta"]["innerInstructions"]) > 0:
            inner_instructions = transaction["meta"]["innerInstructions"]
            if "parsed" in inner_instructions[0]["instructions"][0].keys() and "parsed" in inner_instructions[0]["instructions"][-1].keys():
                try:
                    first_instruction = inner_instructions[0]["instructions"][0]["parsed"]["info"]
                    last_instruction = inner_instructions[0]["instructions"][-1]["parsed"]["info"]
                except:
                    first_instruction = inner_instructions[0]["instructions"][1]["parsed"]["info"]
                    last_instruction = inner_instructions[0]["instructions"][-1]["parsed"]["info"]

                if ("amount" in first_instruction.keys()) and ("amount" in last_instruction.keys()):
                    source_amount = first_instruction["amount"]
                    destination_amount = last_instruction["amount"]
                    source_account = first_instruction["source"]
                    destination_account = last_instruction["destination"]
                    transaction_fees = transaction["meta"]["fee"]
                    signature = transaction["transaction"]["signatures"][0]

                    send = {
                        "source_amount": source_amount, "destination_amount": destination_amount,
                        "source_account": source_account, "destination_account": destination_account,
                        "transaction_fees": transaction_fees, "signature": signature
                    }

                    return send

    return None  # Return None if the criteria are not met


async def retrieve_block_transactions(url):
    """
    Asynchronously retrieves block transactions from a given URL.

    The function continuously attempts to fetch block transactions using the provided URL.

    :param url: The URL of the blockchain API.
    :return: Block transactions if successful, otherwise None.
    """
    while True:
        try:
            async with AsyncClient(url) as client:
                block_number = await stream_data(url)
                blk_transaction = await client.get_block(block_number, "jsonParsed", max_supported_transaction_version=0)
                return blk_transaction
        except:
            pass


async def main():
    """
    Asynchronously fetches and processes transactions from the blockchain's mainnet.

    The function continuously retrieves block transactions, extracts details using retrieve_transaction_details,
    and prints relevant information if the criteria are met.

    Note: Make sure to replace 'mainnet_url' with the actual URL of the mainnet blockchain.

    :return: None
    """
    while True:
        transactions = await retrieve_block_transactions(mainnet_url)
        transactions = json.loads(transactions.to_json())

        for transaction in transactions["result"]["transactions"]:
            data = retrieve_transaction_details(transaction)
            if data is not None:
                # Add additional information to the data dictionary
                data["block_time"] = transactions["result"]["blockTime"]
                # block number is parent slot + 1
                data["block_number"] = transactions["result"]["parentSlot"] + 1
                return data


def run(event, context):
    result = asyncio.run(main())
    x = client.put_record(Record={"Data": json.dumps(
        result)}, DeliveryStreamName="local-serverless-kinesis-firehose")
    logging.info("Data sent to firehose successfully!")
    return x
