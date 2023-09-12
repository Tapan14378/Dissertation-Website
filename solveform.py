from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField


class SolveForm(FlaskForm):
    submit = SubmitField('Solve')

