from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

#Sets up forms for use thorughout the application using Flask-WTF and WTForms
#https://wtforms.readthedocs.io/en/3.2.x/forms/ - Good read on WTForms

# adds forms for login
class LoginForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
# adds forms for registration
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
# adds forms for creating events
class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])
    date = StringField('Event Date', validators=[DataRequired()])
    body = StringField('Event Description', validators=[DataRequired()])
    location = StringField('Event Location', validators=[DataRequired()])
    ##poster = ImageField('Event Poster')  # Assuming you have an ImageField defined
    submit = SubmitField('Create Event')