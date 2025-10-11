from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

#Sets up forms for use thorughout the application using Flask-WTF and WTForms
#https://wtforms.readthedocs.io/en/3.2.x/forms/ - Good read on WTForms

# adds forms for login
class LoginForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# adds forms for registration. Note that 15 is the max length for a phone number
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    phonenumber = StringField('Phone No.', [Length(min=4, max=25)])
    submit = SubmitField('Register')

# adds forms for creating events
class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])
    date = StringField('Event Date', validators=[DataRequired()])
    body = StringField('Event Description', validators=[DataRequired()])
    location = StringField('Event Location', validators=[DataRequired()])
    
    # Added by Ana 
    genre = StringField('Genre', validators=[DataRequired(), Length(max=50)])
    from wtforms import SelectField  # add this import at top of file
    type = SelectField('Type', choices=[
        ('Live Concert','Live Concert'),
        ('Music Festival','Music Festival'),
        ('Orchestra','Orchestra'),
        ('DJ Set','DJ Set'),
        ('Solo Artist Performance','Solo Artist Performance')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('OPEN','OPEN'), ('INACTIVE','INACTIVE'),
        ('SOLD OUT','SOLD OUT'), ('CANCELLED','CANCELLED')
    ], validators=[DataRequired()])
    
    image = StringField('Image path (optional)')
    ##poster = ImageField('Event Poster')  # Assuming you have an ImageField defined
    submit = SubmitField('Create Event')