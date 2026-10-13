"""
Shortage / Surplus Detection and Bike Redistribution Module
Author: Imtiaj Ahmad (Roll: 2207092)
"""

from __future__ import annotations

from typing import List, Dict, Tuple

import pandas as pd


def detect_shortage_surplus(stations: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns shortage and surplus station dataframes based on predicted demand vs available bikes."""
    if stations.empty:
        return pd.DataFrame(columns=['station_id', 'available_bikes', 'predicted_demand', 'gap']), pd.DataFrame(columns=['station_id', 'available_bikes', 'predicted_demand', 'gap'])

    required_cols = {'station_id', 'available_bikes', 'predicted_demand'}
    missing = required_cols - set(stations.columns)
    if missing:
        raise ValueError(f"Missing required columns for redistribution analysis: {sorted(missing)}")

    work_df = stations.copy()
    work_df['available_bikes'] = pd.to_numeric(work_df['available_bikes'], errors='coerce').fillna(0)
    work_df['predicted_demand'] = pd.to_numeric(work_df['predicted_demand'], errors='coerce').fillna(0)
    work_df['gap'] = work_df['predicted_demand'] - work_df['available_bikes']

    shortage = work_df[work_df['gap'] > 0].copy()
    shortage['shortage_bikes'] = shortage['gap']
    shortage = shortage[['station_id', 'available_bikes', 'predicted_demand', 'shortage_bikes']].sort_values(by='shortage_bikes', ascending=False)

    surplus = work_df[work_df['gap'] < 0].copy()
    surplus['surplus_bikes'] = -surplus['gap']
    surplus = surplus[['station_id', 'available_bikes', 'predicted_demand', 'surplus_bikes']].sort_values(by='surplus_bikes', ascending=False)

    return shortage.reset_index(drop=True), surplus.reset_index(drop=True)


def recommend_redistribution(stations: pd.DataFrame) -> List[Dict[str, float | str | int]]:
    """Creates simple redistribution recommendations from surplus stations to shortage stations."""
    shortage_df, surplus_df = detect_shortage_surplus(stations)
    if shortage_df.empty or surplus_df.empty:
        return []

    recommendations: List[Dict[str, float | str | int]] = []
    for _, shortage in shortage_df.iterrows():
        shortage_station = shortage['station_id']
        shortage_qty = int(shortage['shortage_bikes'])

        for _, surplus in surplus_df.iterrows():
            surplus_station = surplus['station_id']
            surplus_qty = int(surplus['surplus_bikes'])
            if surplus_qty <= 0:
                continue

            bikes_to_move = min(shortage_qty, surplus_qty)
            if bikes_to_move <= 0:
                continue

            distance = 1.0
            if {'station_lat', 'station_lon'}.issubset(stations.columns):
                shortage_row = stations[stations['station_id'] == shortage_station].iloc[0]
                surplus_row = stations[stations['station_id'] == surplus_station].iloc[0]
                distance = abs(float(shortage_row['station_lat']) - float(surplus_row['station_lat'])) + abs(float(shortage_row['station_lon']) - float(surplus_row['station_lon']))
                distance = max(distance, 0.5)

            recommendations.append({
                'from_station': str(surplus_station),
                'to_station': str(shortage_station),
                'bikes_to_move': int(bikes_to_move),
                'distance_km': round(float(distance), 2),
                'reason': f"{surplus_station} has surplus bikes and {shortage_station} is under predicted demand"
            })

            shortage_qty -= bikes_to_move
            if shortage_qty <= 0:
                break

    recommendations.sort(key=lambda item: (item['bikes_to_move'], item['distance_km']), reverse=True)
    return recommendations
