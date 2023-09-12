from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeField, IntegerField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired
import csv


class RequestForm(FlaskForm):
    type = RadioField('Type', choices=[('driver', 'Driver'), ('rider', 'Rider'), ('shifter', 'Shifter')],
                      validators=[DataRequired()], coerce=str)
    start_location = StringField('Start Location', validators=[DataRequired()])
    end_location = StringField('End Location', validators=[DataRequired()])
    departure_time = DateTimeField('Departure Time', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    seats = IntegerField('Seats')
    car_pet_friendly = SelectField("Is your car pet friendly?", choices=[('YES', 'Yes'), ('NO', 'No')], default='NO',
                                   coerce=str)
    car_smoker_friendly = SelectField("Is your car smoker friendly?", choices=[('YES', 'Yes'), ('NO', 'No')],
                                      default='NO', coerce=str)
    car_disable_access = SelectField("Does your car have disable access?", choices=[('YES', 'Yes'), ('NO', 'No')],
                                     default='NO', coerce=str)

    pet_preference = SelectField('Pet Preference',
                                 choices=[('YES', 'Want a pet-friendly car'), ('NO', "Don't like pets"),
                                          ('BOTH', 'Any car works')], default='BOTH', coerce=str)
    smoker_preference = SelectField('Smoker Preference',
                                    choices=[('YES', 'Want a smoker-friendly car'), ('NO', "Don't like smokers"),
                                             ('BOTH', 'Any car works')], default='BOTH', coerce=str)
    disable_preference = SelectField('Disable Preference', choices=[('YES', 'Yes'), ('YES', 'No')], default='NO',
                                     coerce=str)

    submit = SubmitField('Submit')

    def validate(self):
        if not super().validate():
            return False

        self.start_location.data = self.start_location.data.upper()
        self.end_location.data = self.end_location.data.upper()

        with open('updated_file.csv', 'r') as f:
            reader = csv.DictReader(f)
            postcodes = [row['postcode'] for row in reader]

        if self.start_location.data not in postcodes:
            self.start_location.errors.append('Invalid start location.')
            return False

        if self.end_location.data not in postcodes:
            self.end_location.errors.append('Invalid end location.')
            return False

        if self.type.data in ['driver', 'shifter'] and self.seats.data is None:
            self.seats.errors.append('Seats is required for driver and shifter.')
            return False

        if self.type.data == 'rider':
            self.seats.data = None

        return True
