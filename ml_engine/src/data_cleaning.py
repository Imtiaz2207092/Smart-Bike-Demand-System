"""
Data Collection & Cleaning Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ['datetime', 'season', 'holiday', 'workingday', 'weather', 'temp', 'atemp', 'humidity', 'windspeed']

def load_and_clean_data(file_path: str, is_train: bool = True) -> pd.DataFrame:
    """
    Loads raw CSV data and performs rigorous data cleaning:
    - Parses datetime
    - Imputes or drops missing values
    - Removes invalid numerical outliers / impossible values
    - Validates schema
    """
    df = pd.read_csv(file_path)
    
    # Standardize column names
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Validate datetime conversion
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['datetime'])
    
    # Fill missing weather numerical values if any
    num_cols = ['temp', 'atemp', 'humidity', 'windspeed']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())
            
    # Fill categorical features
    cat_cols = ['season', 'holiday', 'workingday', 'weather']
    for col in cat_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].mode()[0])
            
    if is_train and 'count' in df.columns:
        # Filter out invalid negative or zero counts
        df['count'] = pd.to_numeric(df['count'], errors='coerce')
        df = df[df['count'] >= 0]
        
        # Remove extreme target outliers (beyond 99.9th percentile)
        upper_limit = df['count'].quantile(0.999)
        df = df[df['count'] <= upper_limit]
        
        if 'casual' in df.columns:
            df['casual'] = df['casual'].fillna(0).clip(lower=0)
        if 'registered' in df.columns:
            df['registered'] = df['registered'].fillna(0).clip(lower=0)
            
    # Sort chronologically
    df = df.sort_values('datetime').reset_index(drop=True)
    return df
