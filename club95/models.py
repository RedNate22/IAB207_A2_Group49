from flask_login import UserMixin
from . import db



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
   events = db.relationship('Event', backref='user')
   # relationship to comments - one to many
   comments = db.relationship('Comment', backref='user')
   # relationship to orders - one to many
   orders = db.relationship('Order', backref='user')

   #Creates a string representation of the User object for easier debugging and logging
   def __repr__(self):
        return f"<User {self.name}>"
   



## setting this up to associate events with users in future
class Event(db.Model):
    # define the name of the table in the database
    __tablename__ = 'events'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    # link event to user - many to one 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # link event to tickets - one to many
    tickets = db.relationship('Ticket', backref='event')
    # relationship to comments - one to many
    comments = db.relationship('Comment', backref='event')

    def __repr__(self):
        return f"<Event {self.title}>"

class Comment(db.Model):
    # define the name of the table in the database
    __tablename__ = 'comments'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text(300))
    commentDateTime = db.Column(db.DateTime)
    # link comment to event and user - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f"<Comment {self.content}>"

class Order(db.Model):
    # define the name of the table in the database
    __tablename__ = 'orders'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    
    # link order to tickets - one to many
    tickets = db.relationship('Ticket', backref='order')
    # link order to user - many to one
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f"<Order {self.id}>"

class Ticket(db.Model):
    # define the name of the table in the database
    __tablename__ = 'tickets'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    ticketTier = db.Column(db.Enum('standard', 'premium', 'vip', 'backstage', name='ticket_tiers'), nullable=False)
    price = db.Column(db.Float)
    availability = db.Column(db.Boolean, default=True)

    # link ticket to order - many to one
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    # link ticket to event - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    def __repr__(self):
        return f"<Ticket {self.ticketTier} - ${self.price}>"

class Genre(db.Model):
    # define the name of the table in the database
    __tablename__ = 'genres'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    genreType = db.Column(db.Enum('electronic', 'jazz' 'indie', 'rock', 'punk'), nullable=False)

    # link genre to events - many to one
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))

    def __repr__(self):
        return f"<Genre {self.genreType}>"

class Artist(db.Model):
    # define the name of the table in the database
    __tablename__ = 'artists'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    artistName = db.Column(db.String(150), unique=True, nullable=False)
    bio = db.Column(db.Text(500), nullable=True)

    # link artist to events - one to many
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    # link artist to genre - one to many
    genres = db.relationship('Genre', backref='artist')

    def __repr__(self):
        return f"<Artist {self.artistName}>"

class Venue(db.Model):
    # define the name of the table in the database
    __tablename__ = 'venues'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    venueName = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # link venue to events - one to many
    events = db.relationship('Event', backref='venue')

    def __repr__(self):
        return f"<Venue {self.venueName}>"
## add additional models if needed here