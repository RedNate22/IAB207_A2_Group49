from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

## define database models, in this case User is inheriting functionality from UserMixin
## UserMixin provides default implementations for the - 
## methods that Flask-Login expects user objects to have.
## https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin
class User(db.Model, UserMixin):
   id = db.Column(db.Integer, primary_key=True)
   email = db.Column(db.String(150), unique=True)
   password = db.Column(db.String(150))
   name = db.Column(db.String(150))
   # events = db.relationship('Event')

## setting this up to associate events with users in future
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    body = db.Column(db.Text)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

## add additional models if needed here