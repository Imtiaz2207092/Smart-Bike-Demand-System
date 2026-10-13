import csv
import datetime
import math
import random
import os

# Set seed for reproducibility
random.seed(42)

STATIONS = [
    {"id": "ST-101", "name": "Central Metro Station", "lat": 23.7771, "lng": 90.3801, "capacity": 50, "type": "commuter"},
    {"id": "ST-102", "name": "University Campus North", "lat": 23.7925, "lng": 90.4078, "capacity": 40, "type": "education"},
    {"id": "ST-103", "name": "Financial District Hub", "lat": 23.7805, "lng": 90.4167, "capacity": 60, "type": "commuter"},
    {"id": "ST-104", "name": "Tech Park East", "lat": 23.8103, "lng": 90.4125, "capacity": 45, "type": "commuter"},
    {"id": "ST-105", "name": "Riverfront Promenade", "lat": 23.7532, "lng": 90.3751, "capacity": 35, "type": "recreational"},
    {"id": "ST-106", "name": "Residential Plaza", "lat": 23.8221, "lng": 90.3654, "capacity": 30, "type": "residential"},
    {"id": "ST-107", "name": "Shopping City Center", "lat": 23.7650, "lng": 90.3890, "capacity": 50, "type": "commercial"},
    {"id": "ST-108", "name": "Suburban Junction", "lat": 23.8350, "lng": 90.4210, "capacity": 35, "type": "residential"},
    {"id": "ST-109", "name": "Hospital Complex", "lat": 23.7410, "lng": 90.3950, "capacity": 30, "type": "commercial"},
    {"id": "ST-110", "name": "Sports Stadium", "lat": 23.8050, "lng": 90.3680, "capacity": 40, "type": "recreational"}
]

def get_season(dt):
    # 1: Spring (Mar-May), 2: Summer (Jun-Aug), 3: Fall (Sep-Nov), 4: Winter (Dec-Feb)
    month = dt.month
    if month in [3, 4, 5]:
        return 1
    elif month in [6, 7, 8]:
        return 2
    elif month in [9, 10, 11]:
        return 3
    else:
        return 4

def is_holiday(dt):
    # Sample Bangladeshi/Global fixed holidays
    holidays = [(1, 1), (2, 21), (3, 26), (4, 14), (5, 1), (12, 16), (12, 25)]
    return 1 if (dt.month, dt.day) in holidays else 0

def generate_row(dt, station):
    season = get_season(dt)
    holiday = is_holiday(dt)
    is_weekend = 1 if dt.weekday() in [4, 5] else 0
    workingday = 0 if (is_weekend or holiday) else 1
    
    hour = dt.hour
    
    # Weather simulation
    temp_base = {1: 24, 2: 32, 3: 28, 4: 18}[season]
    temp_var = 5 * math.sin((hour - 8) * math.pi / 12)
    temp_c = round(temp_base + temp_var + random.uniform(-1.5, 1.5), 1)
    feels_like_c = round(temp_c + random.uniform(-1.0, 2.0), 1)
    
    rain_prob = random.random()
    if rain_prob > 0.92:
        weather_code = 4 # Heavy rain
    elif rain_prob > 0.82:
        weather_code = 3 # Light rain
    elif rain_prob > 0.55:
        weather_code = 2 # Cloudy
    else:
        weather_code = 1 # Clear
        
    humidity_pct = int(max(30, min(98, 65 - temp_var * 2 + (20 if weather_code >= 3 else 0) + random.uniform(-10, 10))))
    wind_speed_kmh = round(max(2.0, min(40.0, 10 + (10 if weather_code >= 3 else 0) + random.uniform(-5, 8))), 1)

    st_type = station["type"]
    cap = station["capacity"]
    
    # Peak hour factors
    if workingday == 1:
        if st_type == "commuter":
            if hour in [8, 9, 17, 18, 19]:
                time_factor = 2.8
            elif 10 <= hour <= 16:
                time_factor = 1.2
            elif 6 <= hour <= 7 or 20 <= hour <= 21:
                time_factor = 1.0
            else:
                time_factor = 0.15
        elif st_type == "education":
            if hour in [9, 10, 15, 16, 17]:
                time_factor = 2.4
            elif 11 <= hour <= 14:
                time_factor = 1.5
            else:
                time_factor = 0.2
        elif st_type == "residential":
            if hour in [7, 8, 18, 19]:
                time_factor = 2.0
            else:
                time_factor = 0.6
        else:
            time_factor = 1.0 if 9 <= hour <= 20 else 0.2
    else:
        if st_type in ["recreational", "commercial"]:
            if 14 <= hour <= 20:
                time_factor = 2.5
            elif 10 <= hour <= 13:
                time_factor = 1.6
            else:
                time_factor = 0.3
        else:
            time_factor = 0.7 if 10 <= hour <= 19 else 0.2

    weather_impact = {1: 1.0, 2: 0.85, 3: 0.45, 4: 0.1}[weather_code]
    base_demand = cap * 0.35 * time_factor * weather_impact
    
    if workingday == 1:
        reg_ratio = 0.82
    else:
        reg_ratio = 0.45
        
    registered_demand = max(0, int(round(base_demand * reg_ratio + random.gauss(0, 2))))
    casual_demand = max(0, int(round(base_demand * (1 - reg_ratio) + random.gauss(0, 1.5))))
    total_demand = registered_demand + casual_demand
    
    available_bikes = max(0, min(cap, int(round(cap * 0.5 + random.uniform(-0.35, 0.35) * cap))))
    net_flow = int(round(random.uniform(-15, 15)))
    
    avail_ratio = available_bikes / cap
    if avail_ratio < 0.20:
        status = "Shortage"
    elif avail_ratio > 0.80:
        status = "Surplus"
    else:
        status = "Balanced"
        
    return {
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "station_id": station["id"],
        "station_name": station["name"],
        "lat": station["lat"],
        "lng": station["lng"],
        "station_capacity": cap,
        "season": season,
        "holiday": holiday,
        "workingday": workingday,
        "weather_code": weather_code,
        "temp_c": temp_c,
        "feels_like_c": feels_like_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kmh": wind_speed_kmh,
        "casual_demand": casual_demand,
        "registered_demand": registered_demand,
        "total_demand": total_demand,
        "available_bikes": available_bikes,
        "net_flow": net_flow,
        "status": status
    }

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(output_dir, "train.csv")
    test_path = os.path.join(output_dir, "test.csv")

    fieldnames = [
        "datetime", "station_id", "station_name", "lat", "lng", "station_capacity",
        "season", "holiday", "workingday", "weather_code", "temp_c", "feels_like_c",
        "humidity_pct", "wind_speed_kmh", "casual_demand", "registered_demand",
        "total_demand", "available_bikes", "net_flow", "status"
    ]

    print("Generating train dataset...")
    start_train = datetime.datetime(2024, 1, 1, 0, 0, 0)
    end_train = datetime.datetime(2024, 8, 31, 23, 0, 0)
    
    with open(train_path, "w", newline="", encoding="utf-8") as f_train:
        writer = csv.DictWriter(f_train, fieldnames=fieldnames)
        writer.writeheader()
        
        curr = start_train
        count = 0
        while curr <= end_train:
            for st in STATIONS:
                row = generate_row(curr, st)
                writer.writerow(row)
                count += 1
            curr += datetime.timedelta(hours=2)
            
    print(f"Generated train.csv with {count} rows at {train_path}")

    print("Generating test dataset...")
    start_test = datetime.datetime(2024, 9, 1, 0, 0, 0)
    end_test = datetime.datetime(2024, 10, 31, 23, 0, 0)
    
    with open(test_path, "w", newline="", encoding="utf-8") as f_test:
        writer = csv.DictWriter(f_test, fieldnames=fieldnames)
        writer.writeheader()
        
        curr = start_test
        count_test = 0
        while curr <= end_test:
            for st in STATIONS:
                row = generate_row(curr, st)
                writer.writerow(row)
                count_test += 1
            curr += datetime.timedelta(hours=2)
            
    print(f"Generated test.csv with {count_test} rows at {test_path}")

if __name__ == "__main__":
    main()
