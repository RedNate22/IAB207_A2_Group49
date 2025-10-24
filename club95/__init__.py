from flask import Flask, session 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pathlib import Path

DATABASE_FILENAME = 'sitedata.sqlite'


# create a db object that is an instance of SQLAlchemy class
db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
   app = Flask(__name__)  # this is the name of the module/package that is calling this app
   # Should be set to false in a production environment
   app.debug = True
   app.secret_key = 'group_49'

   ##Setting up sessions testing as per week 5 tutorial.
   @app.route('/login')
   def set_session():
      session['username'] = 'Bryn'
      return 'Session data set'
   
   @app.route('/getsession')
   def get_session():
      if 'username' in session:
         return session['username']
      return 'no user logged in'
   
   @app.route('/logout')
   def clear_session():
      session.pop('username', None)
      return 'session cleared'
   ## end of session testing segement as per week 5 tutorial

   # ensure the instance folder exists for database storage
   Path(app.instance_path).mkdir(parents=True, exist_ok=True)

   # set the app configuration data - where the db is located "provider://location.name"
   database_path = Path(app.instance_path) / DATABASE_FILENAME
   app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path.as_posix()}"

   # initialise db with flask app
   db.init_app(app)

   Bootstrap5(app)

   db.Model.metadata.clear()
   
   # initialise the login manager
   login_manager = LoginManager()
   
   # set the name of the login function that lets user login
   # in our case it is auth.login (blueprintname.viewfunction name)
   # redirect to login page if user tries to access a login_required page without being logged in
   login_manager.login_view = 'auth_bp.login'
   login_manager.init_app(app)

   # create a user loader function takes userid and returns User
   # Importing inside the create_app function avoids circular references
   # takes the user ID from models and spits back the user object
   # https://speckle.community/t/circular-references-detaching-objects-in-python/3071 - Good read on circular refs in py
   from .models import User
   @login_manager.user_loader
   def load_user(user_id):
      return db.session.scalar(db.select(User).where(User.id==user_id))

   # Import blueprints
   from .home import home_bp 
   app.register_blueprint(home_bp)

   from .user import user_bp
   app.register_blueprint(user_bp)

   from .events import events_bp
   app.register_blueprint(events_bp)

   from .auth import auth_bp
   app.register_blueprint(auth_bp)

   # checks for and then creates database
   _ensure_database(app)
   
   return app

def _ensure_database(app: Flask) -> None:
   """Create the SQLite database on first launch if it doesn't exist."""
   database_path = Path(app.instance_path) / DATABASE_FILENAME
   if database_path.exists():
      return

   with app.app_context():
      db.create_all()
      populate_database(app)

# Populate db with sample events
def populate_database(app: Flask) -> None:
   """Seed multiple sample events, artists, genres, venues, and tickets."""
   from werkzeug.security import generate_password_hash

   with app.app_context():
      from .models import User, Event, Genre, Artist, Ticket, Venue

      # Helper methods
      def get_or_create_genres(name: str) -> Genre:
         """Return an existing genre by name or create a new one if not found."""
         genre = Genre.query.filter_by(genreType=name).first()
         if not genre: 
            genre = Genre(genreType=name)
            db.session.add(genre)
            db.session.flush()
         return genre

      def get_or_create_artist(name: str) -> Artist:
         """Return an existing artist by name or create a new one if not found."""
         artist = Artist.query.filter_by(artistName=name).first()
         if not artist:
            artist = Artist(artistName=name)
            db.session.add(artist)
            db.session.flush()
         return artist

      def get_or_create_venue(name: str, location: str) -> Venue:
         """Return an existing venue by name or create a new one if not found."""
         venue = Venue.query.filter_by(venueName=name).first()
         if not venue:
            venue = Venue(venueName=name, location=location)
            db.session.add(venue)
            db.session.flush()
         return venue
      
      # Create base user for testing and to attach to seeded events
      sample_email = "sample@club95.com"

      user = User.query.filter_by(email=sample_email).first()
      if not user:  
         user = User(
            email=sample_email, 
            password=generate_password_hash("samplepassword", method='scrypt', salt_length=16),
            name="Sample User"
         )

         db.session.add(user)
         db.session.flush()

      # Seed events
      events_seed = [
         # DJ Spreadsheet Live
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
         # Crescent City Players
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
         # Moonlight Resonance
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
         # The Overwhelming Festival
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
         # Optimistic Yeti: Doom Jazz
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
         # Sydney Indie Nights: Local Showcase
         {
            "title": "",
            "type": "",
            "status": "",
            "date": "",
            "description": "",
            "location": "",
            "start_time": "",
            "end_time": "",
            "image": "",
            "venue": {"name": "", "location": ""},
            "genres": ["", "", ""],
            "artists": [""],
            "tickets": [
               {"tier": "", "price": 0.00, "qty": 0}
            ], 
         },
      ]

      # Seed events into db
      for seed in events_seed:
         venue = get_or_create_venue(seed["venue"]["name"], seed["venue"]["location"])

         # Check if event already exists (matching by title)
         event = Event.query.filter_by(title=seed["title"]).first()

         if not event:
            event = Event(
               title=seed["title"],
               type=seed["type"],
               status=seed["status"],
               date=seed["date"],
               description=seed["description"],
               location=seed["location"],
               start_time=seed["start_time"],
               end_time=seed["end_time"],
               image=seed["image"],
               user=user,
               venue=venue,
               genres=[get_or_create_genres(n) for n in seed["genres"]],
               artists=[get_or_create_artist(n) for n in seed["artists"]]
            )

            # attach tickets
            event.tickets = [
               Ticket(ticketTier=t["tier"], price=float(t["price"]), availability=int(t["qty"]))
               for t in seed["tickets"]  # cycle through every ticket defined in seed
            ]

            db.session.add(event)

         else:
            # ? This block could be changed to fill in missing data for seeded events
            # to be more defensive
            print(f"{event.title} already exists!")

      ## ! deprecated
      # # Create or reuse a sample genre/artist/venue
      # genre = Genre.query.filter_by(genreType="Sample").first()
      # if not genre:
      #    genre = Genre(genreType="Sample")
      #    db.session.add(genre)
      #    db.session.flush()

      # artist = Artist.query.filter_by(artistName="Sample Artist").first()
      # if not artist:
      #    artist = Artist(artistName="Sample Artist")
      #    db.session.add(artist)
      #    db.session.flush()

      # venue = Venue.query.filter_by(venueName="Sample Venue").first()
      # if not venue:
      #    venue = Venue(venueName="Sample Venue", location="Sample Location")
      #    db.session.add(venue)
      #    db.session.flush()

      # # Create event (only if it doesn't exist yet)
      # if not Event.query.filter_by(title="Event Test").first():
      #    new_event = Event(
      #       title = "Event Test",
      #       description = "Test description",
      #       date = "01-01-2026",
      #       location = "Test location",
      #       start_time = "00:00",
      #       end_time = "24:00",
      #       type = "Concert",
      #       status = "OPEN",
      #       image = "dj-1.jpg",
      #       user=user,
      #       venue=venue,
      #       genres=[genre],
      #       artists=[artist]
      #    )

      #    # Create tickets
      #    new_event.tickets = [
      #       Ticket(ticketTier="Basic", price=25.0, availability=100, event=new_event),
      #       Ticket(ticketTier="Fan", price=50.0, availability=50, event=new_event),
      #       Ticket(ticketTier="VIP", price=100, availability=5, event=new_event)
      #    ]

      #    # Add sample events to db
      #    db.session.add(new_event)  # stage event(s)
      #    db.session.flush()         # update/insert etc.

      db.session.commit()        # commit to db