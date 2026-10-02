"""
Feature Engineering Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

import pandas as pd
import numpy as np

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts time, weather, cyclical, and domain-specific features
    optimized for bike demand forecasting.
    """
    df = df.copy()
    
    # 1. Temporal Features
    df['hour'] = df['datetime'].dt.hour
    df['month'] = df['datetime'].dt.month
    df['year'] = df['datetime'].dt.year
    df['dayofweek'] = df['datetime'].dt.dayofweek
    df['day_of_year'] = df['datetime'].dt.dayofyear
    df['is_weekend'] = df['dayofweek'].apply(lambda x: 1 if x in [5, 6] else 0)
    
    # 2. Peak Hour Tagging (Crucial for Bike Sharing Systems)
    # Morning Peak: 7 AM - 9 AM | Evening Peak: 5 PM - 7 PM on working days
    def check_peak_hour(row):
        if row['workingday'] == 1:
            if row['hour'] in [7, 8, 9, 17, 18, 19]:
                return 1
        return 0
    df['is_peak_hour'] = df.apply(check_peak_hour, axis=1)
    
    # 3. Cyclical Encoding for Hour and Month
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12.0)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12.0)
    
    # 4. Weather & Environmental Features
    df['temp_diff'] = df['atemp'] - df['temp']
    df['temp_humidity_ratio'] = df['temp'] / (df['humidity'] + 1.0)
    df['is_extreme_weather'] = ((df['weather'] == 4) | (df['windspeed'] > 30)).astype(int)
    
    # 5. Night / Low Demand Hours Tag (11 PM - 5 AM)
    df['is_night_hour'] = df['hour'].apply(lambda h: 1 if h in [23, 0, 1, 2, 3, 4, 5] else 0)
    
    return df

def get_feature_columns() -> list:
    """Returns list of feature column names used for training models."""
    return [
        'season', 'holiday', 'workingday', 'weather',
        'temp', 'atemp', 'humidity', 'windspeed',
        'hour', 'month', 'year', 'dayofweek', 'is_weekend',
        'is_peak_hour', 'is_night_hour',
        'sin_hour', 'cos_hour', 'sin_month', 'cos_month',
        'temp_diff', 'temp_humidity_ratio', 'is_extreme_weather'
    ]
