import pandas as pd
import warnings
from math import radians, sin, cos, sqrt, atan2
import csv
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from forms import RequestForm
from models.models import Request
from solveform import SolveForm
from solver import solve
from extensions import db
from datetime import datetime
from models.models import User


warnings.filterwarnings('ignore')

# Get current date
now = datetime.now()


def get_data_from_db():
    # Fetch data from SQL database
    drivers_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(Request.type == 'driver', Request.departure_time >= now.date()).all()
    riders_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(Request.type == 'rider', Request.departure_time >= now.date()).all()
    shifters_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(Request.type == 'shifter', Request.departure_time >= now.date()).all()

    # Convert data into dictionaries and add the user's name
    drivers_dict = [{**driver[0].to_dict(), "name": driver[1].name} for driver in drivers_data]
    riders_dict = [{**rider[0].to_dict(), "name": rider[1].name} for rider in riders_data]
    shifters_dict = [{**shifter[0].to_dict(), "name": shifter[1].name} for shifter in shifters_data]

    # Convert data into DataFrames
    drivers_df = pd.DataFrame(drivers_dict)
    riders_df = pd.DataFrame(riders_dict)
    shifters_df = pd.DataFrame(shifters_dict)

    return drivers_df, riders_df, shifters_df

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    distance = R * c
    return distance


def has_matching_departure_time(riders_df, drivers_df, shifters_df):
    matching_indices = []
    for rider_idx, rider_row in riders_df.iterrows():
        rider_time = rider_row['departure_time']
        if ((abs(drivers_df['departure_time'] - rider_time) <= pd.Timedelta(minutes=30)).any() or
            (abs(shifters_df['departure_time'] - rider_time) <= pd.Timedelta(minutes=30)).any()):
            matching_indices.append(rider_idx)
    return riders_df.loc[matching_indices]

def has_matching_departure_time_shifter(shifters_df,drivers_df):
    valid_shifter_indices = []
    for shifter_idx, shifter_row in shifters_df.iterrows():
         shifter_time = shifter_row['departure_time']
         if (abs(drivers_df['departure_time'] - shifter_time) <= pd.Timedelta(minutes=30)).any():
             valid_shifter_indices.append(shifter_idx)
    return shifters_df.loc[valid_shifter_indices]


def filter_data_and_save(drivers_df, riders_df, shifters_df):
    # Filter riders based on matching departure times with drivers or shifters
    valid_riders_df = has_matching_departure_time(riders_df, drivers_df, shifters_df)
    # Filter shifter based on matching departure times with drivers
    valid_shifters_df = has_matching_departure_time_shifter(shifters_df, drivers_df)

    # Function to check if a location is within the 1 km radius of any entry in a DataFrame
    def is_within_1km(lat, lon, dataframe):
        for idx, row in dataframe.iterrows():
            if haversine(lat, lon, row['start_lat'], row['start_long']) <= 1.0:
                return True
        return False

    # Filter the driver entries
    valid_driver_indices = []
    for driver_idx, driver_row in drivers_df.iterrows():
        if is_within_1km(driver_row['start_lat'], driver_row['start_long'], valid_riders_df) or is_within_1km(
                driver_row['start_lat'], driver_row['start_long'], valid_shifters_df):
            valid_driver_indices.append(driver_idx)

    # Filter the rider entries
    valid_rider_indices = []
    for rider_idx, rider_row in valid_riders_df.iterrows():
        if is_within_1km(rider_row['start_lat'], rider_row['start_long'], valid_shifters_df):
            valid_rider_indices.append(rider_idx)

    # Filter the shifter entries
    valid_shifter_indices = []
    for shifter_idx, shifter_row in valid_shifters_df.iterrows():
        if is_within_1km(shifter_row['start_lat'], shifter_row['start_long'], drivers_df) or is_within_1km(
                shifter_row['start_lat'], shifter_row['start_long'], valid_riders_df):
            valid_shifter_indices.append(shifter_idx)

    # Create DataFrames with the valid indices
    valid_drivers_df = drivers_df.loc[valid_driver_indices]
    valid_riders_df = valid_riders_df.loc[valid_rider_indices]
    valid_shifters_df = valid_shifters_df.loc[valid_shifter_indices]

    return valid_drivers_df, valid_riders_df, valid_shifters_df
