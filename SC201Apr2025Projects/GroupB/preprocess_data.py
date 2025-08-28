import pandas as pd
import numpy as np
import gym
from gym import spaces
from collections import defaultdict

# 數據讀取和預處理
def load_and_preprocess_data():
    PATH = '/content/drive/MyDrive/Kai/envtest/'
    PATH_TRADING_INDICATOR = PATH+'trading_indicator_without/'
    PATH_STOCK_FEATURES = PATH+'tw_stock_top30/'
    PATH_NEWS_SENTIMENT = PATH+'PTT/'
    PATH_OHLCV = PATH+'OHLCV/'

    TICKERS = [
        "2330", "2317", "2454", "2308", "2382", "2881", "2891", "2882", "2303",
        "2412", "2884", "2886", "3711", "2357", "1216", "2885", "2345", "3231",
        "3034", "2892", "2379", "6669", "2890", "5880", "2880", "2383", "3661",
        "3017", "2883", "3008"
    ]

    marco_df = pd.read_csv(PATH + 'marco_dataset_logdiff.csv')
    industry_df = pd.read_csv(PATH + 'tw_industry_related_dataset.csv')
    stock_data = {}

    for ticker in TICKERS:
        try:
            trading_indicator_df = pd.read_csv(PATH_TRADING_INDICATOR + f'{ticker}.TW.csv')
            stock_df = pd.read_csv(PATH_STOCK_FEATURES + f'{ticker}.TW_data.csv')
            ptt_df = pd.read_csv(PATH_NEWS_SENTIMENT + f'PTT_{ticker}.csv')
            ohlcv_df = pd.read_csv(PATH_OHLCV + f'{ticker}.TW_ohlcv.csv')
            for df in [trading_indicator_df, stock_df, ptt_df, ohlcv_df]:
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                elif 'date' in df.columns:
                    df['Date'] = pd.to_datetime(df['date'])
            merged_df = ohlcv_df.copy()
            if 'Date' in trading_indicator_df.columns:
                merged_df = merged_df.merge(trading_indicator_df, on='Date', how='left')
            if 'Date' in stock_df.columns:
                merged_df = merged_df.merge(stock_df, on='Date', how='left')
            if 'Date' in ptt_df.columns:
                merged_df = merged_df.merge(ptt_df, on='Date', how='left')
            merged_df = merged_df.ffill()
            merged_df = merged_df.dropna()

            stock_data[ticker] = merged_df

        except Exception as e:
            print(f"Error loading data for {ticker}: {e}")
            continue

    return stock_data, marco_df, industry_df
stock_data, marco_df, industry_df = load_and_preprocess_data()
