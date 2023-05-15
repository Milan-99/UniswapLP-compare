import pandas as pd
import ast
import datetime
import csv
import os
from web3 import Web3
from dotenv import load_dotenv
from tqdm import tqdm
from typing import List
#tqdm.pandas()


class Pool_Data():
    def __init__(self, pool: str):
        # Connect to an Ethereum node
        load_dotenv()  # This loads the variables from the .env file
        ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
        self.w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'))
        self.time_register_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "csv", "time_register.csv")
        self.csv_data = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "csv", f"{pool.lower()}.csv"))

    
    def preprocess_data(self, resample=None, remove_outliers=True):
        # Preprocess the data from the CSV, extracting relevant information and converting to appropriate data types
        #data = self.csv_data.join(self.csv_data.progress_apply(self.parse_tokens, axis=1))
        data = self.csv_data.join(self.csv_data.apply(self.parse_tokens, axis=1))
        
        # Uniswap V2
        if 'token0' in data.columns and 'token1' in data.columns:
            data.drop(columns=['token0', 'token1'], inplace=True)

        # Uniswap V3
        if 'inputTokens' in data.columns:
            data.rename(columns={'totalValueLockedUSD': 'reserveUSD', 'inputTokenBalances': 'reserves'}, inplace=True)
            data.loc[:, 'reserve0'] = data['reserves'].apply(lambda x: float(x.split(',')[0].strip("[]'\" ")))
            data.loc[:, 'reserve1'] = data['reserves'].apply(lambda x: float(x.split(',')[1].strip("[]'\" ")))
            data.drop(columns=['reserves'], inplace=True)

            # Assign lastPriceUSD to token0Price and token1Price
            input_tokens = data['inputTokens'].apply(lambda x: ast.literal_eval(x))
            data.loc[:, 'token0Price'] = input_tokens.apply(lambda x: x[0]['lastPriceUSD'])
            data.loc[:, 'token1Price'] = input_tokens.apply(lambda x: x[1]['lastPriceUSD'])
            data.drop(columns=['inputTokens'], inplace=True)

            # Assign cumulativeVolumeUSD to volumeUSD
            data.loc[:, 'volumeUSD'] = data['cumulativeVolumeUSD']
            data.drop(columns=['cumulativeVolumeUSD'], inplace=True)

            # Set volumeToken0 and volumeToken1 to NaN
            data.loc[:, 'volumeToken0'] = float('nan')
            data.loc[:, 'volumeToken1'] = float('nan')
            data.loc[:, 'txCount'] = float('nan')
            data.loc[:, 'createdAtTimestamp'] = float('nan')

            # Extract fee percentage and add it as "swapfee" column
            data.loc[:, 'swapfee'] = data['fees'].apply(lambda x: ast.literal_eval(x)[0]['feePercentage'])
            data.drop(columns=['fees'], inplace=True)

        # Sushiswap
        if 'liquidityUSD' in data.columns and 'reserveUSD' not in data.columns:
            data.loc[:, 'reserveUSD'] = data['liquidityUSD']
            data.drop(columns=['liquidityUSD'], inplace=True)

        numerical_columns = [
            'reserve0', 'reserve1', 'reserveUSD',
            'token0Price', 'token1Price',
            'volumeToken0', 'volumeToken1', 'volumeUSD',
            'txCount', 'createdAtTimestamp', 'blockNumber'
        ]

        for col in numerical_columns:
            data[col] = data[col].astype(float)

        # Update the timestamp register and fetch the required timestamps
        timestamp_register = self.update_timestamp_register(data['blockNumber'].unique())

        # Assign the timestamps to the data DataFrame
        data['timestamp'] = data['blockNumber'].map(timestamp_register['timestamp'].to_dict())

        # Set 'timestamp' as index
        data.set_index('timestamp', inplace=True)

        if resample is not None:
            try:
                data = data.sort_index().resample(resample).last().dropna()
            except:
                print("Resample with correct timeframe!")

        return self.remove_outliers(data, column='volumeUSD') if remove_outliers else data
    
    def remove_outliers(self, data, column, multiplier=1.5):
        data = data[data[column] > 10000]
        # Remove outliers
        Q1 = data[column].quantile(0.01)
        Q3 = data[column].quantile(0.99)
        IQR = Q3 - Q1

        data = data[~((data[column] < (Q1 - multiplier * IQR)) | (data[column] > (Q3 + multiplier * IQR)))]#.reset_index(drop=True)

        return data if not data.empty else None

    def parse_tokens(self, row):
        if 'token0' in row and 'token1' in row:
            token0 = ast.literal_eval(row['token0'])
            token1 = ast.literal_eval(row['token1'])
            return pd.Series({
                'token0_id': token0['id'],
                'token0_symbol': token0['symbol'],
                'token0_decimals': token0['decimals'],
                'token1_id': token1['id'],
                'token1_symbol': token1['symbol'],
                'token1_decimals': token1['decimals']
            })
        elif 'inputTokens' in row:
            input_tokens = ast.literal_eval(row['inputTokens'])
            token0 = input_tokens[0]
            token1 = input_tokens[1]
            return pd.Series({
                'token0_id': token0['id'],
                'token0_symbol': token0['symbol'],
                'token0_decimals': token0['decimals'],
                'token1_id': token1['id'],
                'token1_symbol': token1['symbol'],
                'token1_decimals': token1['decimals']
            })
    
    def update_timestamp_register(self, block_numbers):
        file_path = self.time_register_path

        if os.path.exists(file_path):
            timestamp_register = pd.read_csv(file_path, index_col='blockNumber')
        else:
            timestamp_register = pd.DataFrame(columns=['timestamp'], index=pd.Index([], name='blockNumber'))

        # Identify the missing block numbers
        missing_block_numbers = set(block_numbers) - set(timestamp_register.index)

        # Fetch the missing timestamps and update the register
        if len(missing_block_numbers) > 0:
            missing_timestamps = {}
            for bn in tqdm(missing_block_numbers, desc="Fetching missing timestamps"):
                missing_timestamps[bn] = datetime.datetime.fromtimestamp(self.w3.eth.get_block(int(bn))['timestamp'])
            new_timestamps_df = pd.DataFrame.from_dict(missing_timestamps, orient='index', columns=['timestamp']).rename_axis('blockNumber')
            timestamp_register = pd.concat([timestamp_register, new_timestamps_df])
            # Save the updated register to the file
            timestamp_register.to_csv(file_path, index=True)

        return timestamp_register
    
    def read_existing_csv(self, filename: str) -> List[dict]:
        if not os.path.exists(filename):
            return []

        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return reader
