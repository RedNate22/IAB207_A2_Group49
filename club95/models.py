from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired



## define database models, in this case User is inheriting functionality from UserMixin
## UserMixin provides default implementations for the - 
## methods that Flask-Login expects user objects to have.
## https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin
class User(db.Model, UserMixin):
   # define the name of the table in the database
   __tablename__ = 'users'

   # define the columns of the table
   id = db.Column(db.Integer, primary_key=True)
   email = db.Column(db.String(150), unique=True)
   password = db.Column(db.String(150))
   name = db.Column(db.String(150))
   phoneNumber = db.Column(db.String(20), nullable=True)
   # relationship to events - one to many 
   events = db.relationship('Event')
   # relationship to comments - one to many
   comments = db.relationship('comment')
   # relationship to orders - one to many
   orders = db.relationship('order')



## setting this up to associate events with users in future
class Event(db.Model):
    # define the name of the table in the database
    __tablename__ = 'events'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    ## TODO: add validation to ensure date isn't in the past
    ## not sure if I added this datetime correctly or not
    date = db.Column(db.dateTime)
    body = db.Column(db.Text(300))
    location = db.Column(db.String(150))
    image = db.Column(db.String(150), nullable=True, default='./static/img/yeti.png')
    # link event to user - many to one 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # link event to tickets - one to many
    tickets = db.relationship('ticket')
    # relationship to comments - one to many
    comments = db.relationship('comment')

class comment(db.Model):
    # define the name of the table in the database
    __tablename__ = 'comments'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text(300))
    commentDateTime = db.Column(db.dateTime)
    # link comment to event and user - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class order(db.Model):
    # define the name of the table in the database
    __tablename__ = 'orders'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.dateTime)
    amount = db.Column(db.Float)
    
    # link order to tickets - one to many
    tickets = db.relationship('ticket')
    # link order to user - many to one
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ticket(db.Model):
    # define the name of the table in the database
    __tablename__ = 'tickets'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    ticketTier = db.Column(db.Enum(150))
    price = db.Column(db.Float)
    availability = db.Column(db.Boolean, default=True)

    # link ticket to order - many to one
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    # link ticket to event - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

class genre(db.Model):
    # define the name of the table in the database
    __tablename__ = 'genres'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    genreType = db.Column(db.enum, unique=True, nullable=False)

    # link genre to events - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))

class artist(db.Model):
    # define the name of the table in the database
    __tablename__ = 'artists'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    artistName = db.Column(db.String(150), unique=True, nullable=False)
    bio = db.Column(db.Text(500), nullable=True)

    # link artist to events - one to many
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    # link artist to genre - one to many
    genres = db.relationship('genre')

class venue(db.Model):
    # define the name of the table in the database
    __tablename__ = 'venues'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    venueName = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # link venue to events - one to many
    events = db.relationship('event')
## add additional models if needed here