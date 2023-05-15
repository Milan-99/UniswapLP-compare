import requests
import json
import csv
import argparse
import os
from typing import List
from dotenv import load_dotenv
from tqdm import tqdm
tqdm.pandas()

### User variables


pools = [
    {"id": "0x06da0fd433c1a5d7a4faa01111c044910a184553", "dex_name": "SushiV2"},
    {"id": "0x21b8065d10f73ee2e260e5b47d3344d3ced7596e", "dex_name": "UniV2"},
    {"id": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0", "dex_name": "SushiV2"},
    {"id": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f", "dex_name": "UniV2"},
    {"id": "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11", "dex_name": "UniV2"},
    {"id": "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5", "dex_name": "UniV2"},
    {"id": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc", "dex_name": "UniV2"},
    {"id": "0xbb2b8038a1640196fbe3e38816f3e67cba72d940", "dex_name": "UniV2"},
    {"id": "0xccb63225a7b19dcf66717e4d40c9a72b39331d61", "dex_name": "UniV2"},
    {"id": "0xceff51756c56ceffca006cd410b03ffc46dd3a58", "dex_name": "SushiV2"},
    
]



### Functions

def create_days_list(existing_block_numbers: List[int] = []) -> List[int]:
    one_day = 2000
    from_timestamp = 10042267
    to_timestamp = 17220571 

    daily_blocks_list = []
    while from_timestamp < to_timestamp:
        if to_timestamp not in existing_block_numbers:
            daily_blocks_list.append(to_timestamp)
        to_timestamp -= one_day
    return daily_blocks_list

def query_the_graph(pair_id: str, block_number: int, dex_name: str) -> dict: 
    if dex_name.lower() == "univ2":
        url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
        query = f"""
            query {{
            pair(id: "{pair_id.lower()}", block: {{number: {block_number}}}) {{
                id
                token0 {{
                    id
                    symbol
                    decimals
                }}
                token1 {{
                    id
                    symbol
                    decimals
                }}
                reserve0
                reserve1
                reserveUSD
                token0Price
                token1Price
                volumeToken0
                volumeToken1
                volumeUSD
                txCount
                createdAtTimestamp
            }}
            }}
            """
    elif dex_name.lower() == "univ3":
        load_dotenv()
        THEGRAPH_API_KEY = os.environ['THEGRAPH_API_KEY']
        url = f"https://gateway.thegraph.com/api/{THEGRAPH_API_KEY}/subgraphs/id/ELUcwgpm14LKPLrBRuVvPvNKHQ9HvwmtKgKSH6123cr7"
        query = f"""
            query {{
            liquidityPool(id: "{pair_id.lower()}", block: {{number: {block_number}}}) {{
                id
                totalValueLockedUSD
                cumulativeVolumeUSD
                rewardTokenEmissionsUSD
                inputTokenWeights
                inputTokenBalances
                inputTokens {{
                    id
                    symbol
                    decimals
                    lastPriceUSD
                }}
                fees {{
                    feeType
                    feePercentage
                }}
            }}
            }}
            """
    elif dex_name.lower() == "sushiv2":
        url = "https://api.thegraph.com/subgraphs/name/sushi-v2/sushiswap-ethereum"
        query = f"""
            query {{
            pair(id: "{pair_id.lower()}", block: {{number: {block_number}}}) {{
                id
                token0 {{
                id
                symbol
                decimals
                }}
                token1 {{
                id
                symbol
                decimals
                }}
                reserve0
                reserve1
                liquidityUSD
                token0Price
                token1Price
                volumeToken0
                volumeToken1
                volumeUSD
                txCount
                createdAtTimestamp
            }}
            }}
            """
    else:
        raise ValueError("Invalid dex_name provided. Choose either 'uniswap' or 'sushiswap' not", dex_name)

    headers = {"Content-Type": "application/json"}
    data = {"query": query}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}")

def save_to_csv(filename: str, rows: List[dict]):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = set().union(*(row.keys() for row in rows))
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print("Successfully saved output!")


def read_existing_csv(filename: str, dex_name: str) -> List[dict]:
    if not os.path.exists(filename):
        return []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [{"exchange": dex_name.lower(), **row} for row in reader]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair_id", help="Pair id to use for the query.", default=None)
    parser.add_argument("--dex_name", help="Decentralized exchange name.", default=None)
    args = parser.parse_args()

    for pool in pools:
        if args.pair_id:
            pool_id = args.pair_id
        else:
            pool_id = pool["id"]

        if args.dex_name:
            dex_name = args.dex_name
        else:
            dex_name = pool["dex_name"]

        output_file = f"csv/{pool_id.lower()}.csv"
        existing_csv_rows = read_existing_csv(output_file, dex_name)
        existing_block_numbers = [int(row['blockNumber']) for row in existing_csv_rows]
        block_numbers = create_days_list(existing_block_numbers)
        new_csv_rows = []

        with tqdm(block_numbers, desc=f"{dex_name}: {pool['id']} | Fetching blocks", unit="block") as progress_bar:
            for block_number in progress_bar:
                try:                    
                    result = query_the_graph(pool_id, block_number, dex_name)
                    progress_bar.set_description(f"{pool['id']}: Fetched block number {block_number}")
                    progress_bar.refresh()
                    pair_data = result['data']['pair'] if dex_name.lower() != "UniV3" else result['data']['liquidityPool']
                    pair_data['blockNumber'] = block_number
                    pair_data['exchange'] = dex_name.lower()
                    new_csv_rows.append(pair_data)
                except Exception as e:
                    print(f"Error: {e}")
                    break

        all_csv_rows = existing_csv_rows + new_csv_rows
        all_csv_rows.sort(key=lambda x: int(x['blockNumber']))

        save_to_csv(output_file, all_csv_rows)


  
