import csv
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from forms import RequestForm
from models.models import Request
from solveform import SolveForm
from solver import solve
from extensions import db
from models.models import User
from datetime import datetime


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('auth.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name)


@main.route('/form', methods=['GET', 'POST'])
@login_required
def form():
    request_form = RequestForm()
    if request.method == 'POST' and request_form.validate():
        if request_form.validate():
            request_type = request_form.type.data
            start_location = request_form.start_location.data
            end_location = request_form.end_location.data
            departure_time = request_form.departure_time.data
            if request_type == 'rider':
                pet = request_form.pet_preference.data
                smoker = request_form.smoker_preference.data
                disable = request_form.disable_preference.data
                seats = None  # Define seats as None for rider requests
            else:
                seats = int(request_form.seats.data)
                pet = request_form.car_pet_friendly.data
                smoker = request_form.car_smoker_friendly.data
                disable = request_form.car_disable_access.data

            start_lat, start_long = None, None
            end_lat, end_long = None, None
            # Fetch latitude and longitude from the file
            with open('updated_file.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['postcode'] == start_location:
                        start_lat, start_long = float(row['Latitude']), float(row['Longitude'])
                    if row['postcode'] == end_location:
                        end_lat, end_long = float(row['Latitude']), float(row['Longitude'])

            if start_lat is None or start_long is None:
                flash(f'Could not find start location: {start_location}')
                return redirect(url_for('main.form'))

            if end_lat is None or end_long is None:
                flash(f'Could not find end location: {end_location}')
                return redirect(url_for('main.form'))

            request_entry = Request(
                user_id=current_user.id,
                type=request_type,
                start_location=start_location,
                start_lat=start_lat,
                start_long=start_long,
                end_location=end_location,
                end_lat=end_lat,
                end_long=end_long,
                departure_time=departure_time,
                seats=seats,
                pet=pet,
                smoker=smoker,
                disable=disable
            )

            print("Before adding to session:", db.session.new)
            db.session.add(request_entry)
            print("After adding to session:", db.session.new)
            db.session.commit()

            flash('Your request has been submitted!', 'success')
            return redirect(url_for('main.dashboard'))
    else:
        for field, errors in request_form.errors.items():
            for error in errors:
                flash(error, 'error')

    return render_template('request_form.html', form=request_form)


from datetime import date


@main.route('/solve', methods=['GET', 'POST'])
@login_required
def solve_route():
    result = None
    today = date.today()
    current_time = datetime.now()
    if request.method == 'POST':
        print("Inside solve_route function")
        tolerance = 1

        # Fetch data from SQL database
        drivers_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(
            Request.type == 'driver', Request.departure_time >= today).all()
        riders_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(
            Request.type == 'rider', Request.departure_time >= today).all()
        shifters_data = db.session.query(Request, User).join(User, User.id == Request.user_id).filter(
            Request.type == 'shifter', Request.departure_time >= today).all()

        # Convert data into dictionaries and add the user's name
        drivers_dict = [{**driver[0].to_dict(), "name": driver[1].name} for driver in drivers_data]
        riders_dict = [{**rider[0].to_dict(), "name": rider[1].name} for rider in riders_data]
        shifters_dict = [{**shifter[0].to_dict(), "name": shifter[1].name} for shifter in shifters_data]

        if drivers_dict or riders_dict or shifters_dict:
            result = solve(tolerance, drivers_dict, riders_dict, shifters_dict)
            print("Solving process completed")

        if not result:
            flash('We are sorry; there is currently no matching request found.', 'error')

        return render_template('solve_form.html', results=result, current_time=current_time)

    form = SolveForm()
    return render_template('solve_form.html', form=form, current_time=current_time)
