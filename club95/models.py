from flask_login import UserMixin
from . import db
from sqlalchemy.ext.associationproxy import association_proxy



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
    firstName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    phoneNumber = db.Column(db.String(20), nullable=True)
    streetAddress = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text(300), nullable=True)
    profilePicture = db.Column(db.String(200), nullable=True)
    # relationship to events - one to many 
    events = db.relationship('Event', backref='user')
    # relationship to comments - one to many
    comments = db.relationship('Comment', backref='user')
    # relationship to orders - one to many
    orders = db.relationship('Order', backref='user')

    #Creates a string representation of the User object for easier debugging and logging
    def __repr__(self):
        first = self.firstName or ''
        last = self.lastName or ''
        full_name = f"{first} {last}".strip()
        return f"<User {full_name}>"


# Association table for many-to-many relationship between Event and Artist
class EventArtist(db.Model):
    __tablename__ = 'event_artist'

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    set_time = db.Column(db.String(5), nullable=True)

    event = db.relationship('Event', back_populates='artist_links')
    artist = db.relationship('Artist', back_populates='event_links')

# Association table for many-to-many relationship between Event and Genre
event_genre = db.Table(
    'event_genre',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

## setting this up to associate events with users in future
class Event(db.Model):
    # define the name of the table in the database
    __tablename__ = 'events'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genres = db.relationship('Genre', secondary=event_genre, backref='events')
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(200), nullable=True)

    start_time = db.Column(db.String(10), nullable=True)
    end_time = db.Column(db.String(10), nullable=True)

    # relationship to event images - so that events can have multiple images
    images = db.relationship("EventImage", back_populates="event", cascade="all, delete-orphan")

    # link event to user - many to one 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    # link event to tickets - one to many
    tickets = db.relationship('Ticket', backref='event')
    # relationship to comments - one to many
    comments = db.relationship('Comment', backref='event')
    # many-to-many relationship with artists
    artist_links = db.relationship('EventArtist', back_populates='event', cascade='all, delete-orphan')
    artists = association_proxy('artist_links', 'artist')

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

class OrderTicket(db.Model):
    __tablename__ = 'order_ticket'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)
    # orders to tickets relationships defined below
    order = db.relationship('Order', back_populates='line_items')
    ticket = db.relationship('Ticket', back_populates='order_links')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tickets = db.relationship(
        'Ticket',
        secondary='order_ticket',
        back_populates='orders',
        overlaps='line_items,order,ticket'
    )
    line_items = db.relationship(
        'OrderTicket',
        back_populates='order',
        cascade='all, delete-orphan',
        overlaps='tickets'
    )

    def __repr__(self):
        return f"<Order {self.id}>"

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    ticketTier = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Integer, default=1, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    orders = db.relationship(
        'Order',
        secondary='order_ticket',
        back_populates='tickets',
        overlaps='order_links,line_items,order'
    )
    order_links = db.relationship(
        'OrderTicket',
        back_populates='ticket',
        cascade='all, delete-orphan',
        overlaps='orders,tickets'
    )

    def __repr__(self):
        return f"<Ticket {self.ticketTier} (${self.price}) x{self.availability}"

class Genre(db.Model):
    # define the name of the table in the database
    __tablename__ = 'genres'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    genreType = db.Column(db.String(50), nullable=False)

    # link genre to events - many to one
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))

    def __repr__(self):
        return f"<Genre {self.genreType}>"

class Artist(db.Model):
    # define the name of the table in the database
    __tablename__ = 'artists'
    # define the columns of the table
    id = db.Column(db.Integer, primary_key=True)
    artistName = db.Column(db.String(150), unique=True, nullable=False)
    # many-to-many relationship with events
    event_links = db.relationship('EventArtist', back_populates='artist', cascade='all, delete-orphan')
    events = association_proxy('event_links', 'event')
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
class EventImage(db.Model):
    __tablename__ = "event_images"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, nullable=True)

    event = db.relationship("Event", back_populates="images")





## add additional models if needed here