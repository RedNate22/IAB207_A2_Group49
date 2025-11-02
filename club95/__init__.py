# import flask - from 'package' import 'Class'
from datetime import datetime, timedelta
from flask import Flask, app, render_template 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pathlib import Path
from sqlalchemy import func
from werkzeug.exceptions import HTTPException, InternalServerError
from urllib.parse import quote_plus

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

   # centralised error handling for HTTP and generic exceptions
   def _render_error_page(error):
      # Render the shared error template for both HTTP and unhandled exceptions.
      if isinstance(error, HTTPException):
         handled_error = error
         status_code = error.code
      # Handle unhandled exceptions
      else:
         handled_error = InternalServerError(original_exception=error)
         status_code = 500
      # return error details for rendering
      return render_template("error.html", error=handled_error), status_code

   import traceback

   @app.errorhandler(Exception)
   def debug_all(e):
      print("\n=== TRACEBACK START ===")
      traceback.print_exc()
      print("=== TRACEBACK END ===\n")
      return _render_error_page(e)

   # register error handlers
   # TODO uncomment
   # app.register_error_handler(HTTPException, _render_error_page)
   # app.register_error_handler(Exception, _render_error_page)

   # Intentional error route for testing
   # * uncomment to test
   # @app.route("/force-500")
   # def force_500():
   #    raise RuntimeError("Intentional failure for testing.")
   
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
   login_manager.login_message = 'Please log in to continue.'
   login_manager.login_message_category = 'warning'
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
   
 # -------------------------------------------------------------
   # Context Processor for Dynamic Filter Options
   # -------------------------------------------------------------
   # This function runs before every template render and injects
   # shared data into all templates (similar to a global variable).
   # In this case, it provides the list of event types, genres,
   # and statuses directly from the database. 
   #
   # This allows dropdown filters in the HTML (e.g. homepage, 
   # My Events, My Tickets) to display dynamic options 
   # based on the data actually stored in the database, 
   # rather than hardcoding them.
   #
   # Reference: https://flask.palletsprojects.com/en/3.0.x/templating/#context-processors
   # -------------------------------------------------------------

   from .models import Genre, EventType  # import models used to fetch data

   @app.context_processor
   def inject_filter_options():
       try:
           # Query all event types and genres from the database
           event_types = EventType.query.order_by(EventType.typeName).all()
           genres = Genre.query.order_by(Genre.genreType).all()
       except Exception:
           # If tables are missing or database not yet created, avoid errors
           event_types, genres = [], []

       # Define a static list of possible event statuses for filtering
       statuses = ['OPEN', 'INACTIVE', 'SOLD OUT', 'CANCELLED']

       # Return these as a dictionary so they are available to every template
       return {
           'filter_event_types': event_types,
           'filter_genres': genres,
           'filter_statuses': statuses
       }


   return app

def _ensure_database(app: Flask) -> None:
   # Create the SQLite database on first launch if it doesn't exist.
   database_path = Path(app.instance_path) / DATABASE_FILENAME
   if database_path.exists():
      return

   with app.app_context():
      db.create_all()
      populate_database(app)

# Populate db with sample events
def populate_database(app: Flask) -> None:
   # Seed database with a sample user, events, artists, genres, venues, tickets and event types.
   from werkzeug.security import generate_password_hash

   with app.app_context():
      from .models import (
         User,
         Event,
         Genre,
         Artist,
         Ticket,
         Venue,
         EventType,
         Comment,
         Order,
         OrderTicket,
      )

      # Helper methods
      def get_or_create_type(name: str) -> EventType:
         # Return an existing event type by name or create a new one if not found.
         # Remove trailing/leading whitespace 
         cleaned = (name or "").strip()
         if not cleaned:
            return None
         
         event_type = EventType.query.filter_by(typeName=cleaned).first()
         if not event_type:
            event_type = EventType(typeName=cleaned)
            db.session.add(event_type)
            db.session.flush()
         return event_type

      # Declare base event types
      base_event_types = [
         "Live Concert",
         "Music Festival",
         "Orchestra",
         "DJ Set",
         "Solo Artist Performance",
         ]

      # Add base types to db
      for typeName in base_event_types:
         get_or_create_type(typeName)

      def get_or_create_genres(name: str) -> Genre:
         # Return an existing genre by name or create a new one if not found.
         genre = Genre.query.filter_by(genreType=name).first()
         if not genre: 
            genre = Genre(genreType=name)
            db.session.add(genre)
            db.session.flush()
         return genre

      # Declare base genres 
      base_event_genres = [
         "Alternative",
         "Blues",
         "Classical",
         "Contemporary Orchestral",
         "Electronic",
         "Experimental",
         "Funk",
         "Fusion",
         "Indie",
         "Jazz",
         "Metal",
         "Pop",
         "Punk",
         "Rock",
         "Swing",
         "Synthwave",
         "Techno",
         ]

      # Add base genres to db
      for genreName in base_event_genres:
         get_or_create_genres(genreName)

      def get_or_create_artists(name: str) -> Artist:
         # Return an existing artist by name or create a new one if not found.
         artist = Artist.query.filter_by(artistName=name).first()
         if not artist:
            artist = Artist(artistName=name)
            db.session.add(artist)
            db.session.flush()
         return artist

      def build_map_embed(address: str) -> str:
         cleaned = (address or "").strip()
         if not cleaned:
            return ""
         return f"https://www.google.com/maps?q={quote_plus(cleaned)}&output=embed"

      def get_or_create_venue(name: str, location: str) -> Venue:
         # Return an existing venue for the supplied name/location, creating one if needed.
         primary_location = (location or "").strip()
         fallback_name = (name or "").strip()
         lookup_value = primary_location or fallback_name
         if not lookup_value:
            return None

         venue = Venue.query.filter(func.lower(Venue.location) == lookup_value.lower()).first()
         if not venue:
            venue = Venue(location=lookup_value, venueMap=build_map_embed(lookup_value))
            db.session.add(venue)
            db.session.flush()
         elif not venue.venueMap:
            venue.venueMap = build_map_embed(lookup_value)
         return venue

      def normalise_unique(values):
         # Strip empty strings and return unique names preserving order.
         seen = set()
         results = []
         for value in values or []:
            name = (value or "").strip()
            if not name:
               continue
            key = name.lower()
            if key in seen:
               continue
            seen.add(key)
            results.append(name)
         return results
      
      # Create base user for testing and to attach to seeded events
      sample_email = "sample@club95.com"

      user = User.query.filter_by(email=sample_email).first()
      if not user:  
         user = User(
            email=sample_email, 
            password=generate_password_hash("samplepassword", method='scrypt', salt_length=16),
            firstName="John",
            lastName="Doe",
            phoneNumber="0412345678",
            streetAddress="123 Sample St, Brisbane QLD 4000",
            bio="My Name is John Doe and I love attending events!",
            
         )

         db.session.add(user)
         db.session.flush()

      # Sample comment content for the first three seeded events
      comment_batches = {
         "DJ Spreadsheet Live": [
            "Cannot wait to hear those pivot tables drop!",
            "Do we need to bring our own spreadsheets?",
            "Heard last year's closer was a VLOOKUP solo."
         ],
         "Crescent City Players": [
            "Booked a table for four—going to be a great night.",
            "Love this lineup, especially Mojo Webb!",
            "If anyone needs a carpool from the city, let me know.",
            "Do they still do that encore medley?"
         ],
         "Moonlight Resonance": [
            "Perfect excuse for a riverside picnic beforehand.",
            "Bringing the family—kids are obsessed with the strings."
         ],
      }

      def seed_sample_orders(event: Event, tickets_by_tier: dict[str, Ticket]) -> None:
         """Attach example orders to the provided event if it matches seed targets."""
         if event.title not in {"DJ Spreadsheet Live", "Crescent City Players", "Moonlight Resonance"}:
            return

         # Avoid duplicate seeding on reruns
         existing_orders = {
            ot.order
            for ticket in event.tickets
            for ot in ticket.order_links
         }
         if existing_orders:
            return

         order_samples = []
         if event.title == "DJ Spreadsheet Live":
            ticket = tickets_by_tier.get("1")
            if ticket:
               order_samples.append({"ticket": ticket, "qty": 2})
         elif event.title == "Crescent City Players":
            tier_two = tickets_by_tier.get("2")
            tier_three = tickets_by_tier.get("3")
            if tier_two:
               order_samples.append({"ticket": tier_two, "qty": 1})
            if tier_three:
               order_samples.append({"ticket": tier_three, "qty": 2})
         elif event.title == "Moonlight Resonance":
            ticket = tickets_by_tier.get("Standard")
            if ticket:
               order_samples.append({"ticket": ticket, "qty": 3})

         if not order_samples:
            return

         for index, sample in enumerate(order_samples, start=1):
            ticket = sample["ticket"]
            qty = max(1, int(sample["qty"]))
            total = ticket.price * qty
            order = Order(
               order_date=datetime.now() - timedelta(hours=index),
               amount=total,
               user=user,
            )
            db.session.add(order)
            db.session.flush()

            # Link order and ticket
            link = OrderTicket(
               order_id=order.id,
               ticket_id=ticket.id,
               quantity=qty,
               price_at_purchase=ticket.price,
            )
            db.session.add(link)

            # Reduce availability to simulate purchase
            if ticket.availability is not None:
               ticket.availability = max(0, ticket.availability - qty)

      # Seed events
      events_seed = [
         # DJ Spreadsheet Live
         {
            "title": "DJ Spreadsheet Live",
            "type": "DJ Set",
            "status": "CANCELLED",
            "date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Watch DJ Spreadsheet seamlessly mix quarterly reports into smooth beats. Free Wi-Fi included.",
            "start_time": "09:00",
            "end_time": "17:00",
            "image": "dj-1.jpg",
            "venue": {"name": "Conference Room B, Novotel Brisbane", "location": ""},  # ? is location a FK?
            "genres": ["Electronic", "Techno", "Synthwave"],
            "artists": ["DJ Spreadsheet"],
            "tickets": [
               {"tier": "1", "price": 5.00, "perks": "1 unpaid lunch break", "qty": 30}
            ], 
         },
         # Crescent City Players
         {
            "title": "Crescent City Players",
            "type": "Live Concert",
            "status": "OPEN",
            "date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": 
               "An intimate evening of smooth jazz and improvisation, featuring local hit talent, " + 
               "Crescent City Players, joined by The Walters and Mojo Webb. Enjoy classic standards and modern tunes " + 
               "in a cozy, relaxed setting",
            "start_time": "13:00",
            "end_time": "15:00",
            "image": "crescent-city-players-poster-horizontal.jpg",
            "venue": {"name": "Royal Mail Hotel", "location": "92 Brisbane Terrace Goodna, QLD 4300"},
            "genres": ["Jazz", "Swing", "Fusion"],
            "artists": ["Crescent City Players", "The Walters", "Mojo Webb"],
            "tickets": [
               {"tier": "1", "price": 0.00, "perks": "", "qty": 30},
               {"tier": "2", "price": 7.99, "perks": "1 free drink of choice", "qty": 20},
               {"tier": "3", "price": 14.99, "perks": "2 free drinks of choice", "qty": 10},
               {"tier": "4", "price": 24.99, "perks": "2 free drinks of choice & priority seating", "qty": 5},
               {"tier": "5", "price": 49.99, "perks": "VIP (unlimited drinks, meet and greet with the bands)", "qty": 1},
            ], 
         },
         # Moonlight Resonance
         {
            "title": "Moonlight Resonance",
            "type": "Orchestra",
            "status": "OPEN",
            "date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
            "description": 
               "A riverside orchestral showcase blending timeless symphonies " +
               "with modern composition.",
            "start_time": "19:00",
            "end_time": "20:00",
            "image": "orchestra.jpg",
            "venue": {"name": "Riverside Pavilion", "location": "Brisbane QLD"},
            "genres": ["Classical", "Contemporary", "Orchestral"],
            "artists": ["Commonwealth Orchestra"],
            "tickets": [
               {"tier": "Standard", "price": 32.00, "perks": "", "qty": 130}
            ], 
         },
         # The Overwhelming Festival
         {
            "title": "The Overwhelming Festival",
            "type": "Music Festival",
            "status": "OPEN",
            "date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "description": 
               "Three stages, 600 bands, 30 taco trucks, 1 working portaloo. " +
               "An afternoon to remember (or forget).",
            "start_time": "12:00",
            "end_time": "24:00",
            "image": "festival.jpg",
            "venue": {"name": "Abandoned Bunnings Warehouse", "location": "Perth"},
            "genres": ["Pop", "Electronic", "Techno", "Indie"],
            "artists": ["Do I really need to list all 600?"],
            "tickets": [
               {"tier": "Portaloo Enjoyer", "price": 5.05, "perks": "", "qty": 5000},
               {"tier": "Taco Tuesday", "price": 12.05, "perks": "1 free taco", "qty": 100}
            ], 
         },
         # Optimistic Yeti: Doom Jazz
         {
            "title": "Optimistic Yeti: Doom Jazz",
            "type": "Solo Artist Performance",
            "status": "SOLD OUT",
            "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "description": 
               "The elusive Optimistic Yeti descends from the Blue Mountains once a year to " +
               "perform a doom jazz set that critics describe as \"The kind of music you hear " +
               "right before a haunted elevator drops.\" ",
            "start_time": "00:00",
            "end_time": "24:00",
            "image": "yeti.jpg",
            "venue": {"name": "Aisle 12 (frozen foods)", "location": "24/7 IGA"},
            "genres": ["Experimental", "Jazz", "Metal"],
            "artists": ["Optimistic Yeti"],
            "tickets": [
               {"tier": "Yeti fan", "price": 999.999, "perks": "IGA parking", "qty": 0}
            ], 
         },
         # Sydney Indie Nights: Local Showcase
         {
            "title": "Sydney Indie Nights: Local Showcase",
            "type": "Live Concert",
            "status": "INACTIVE",
            "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "description": "A lineup of Sydney's top emerging indie and alternative bands, " +
            "offerning an energetic night of original music and live performances.",
            "start_time": "20:00",
            "end_time": "23:00",
            "image": "indie-band.jpg",
            "venue": {"name": "The Enmore Theatre", "location": "NSW"},
            "genres": ["Indie", "Rock", "Alternative"],
            "artists": [
               "Finlay's Starlights", "Sour Tart", "Dead Gear", "Lead Donkeys",
               "Bitter Sweet's", "and more!"],
            "tickets": [
               {"tier": "Basic", "price": 10.50, "perks": "", "qty": 100},
               {"tier": "VIP", "price": 90.50, "perks": "VIP meet and greet with the bands", "qty": 5},
            ], 
         },
      ]

      # Seed events into db
      for seed in events_seed:
         venue = get_or_create_venue(seed["venue"]["name"], seed["venue"]["location"])

         # Check if event already exists (matching by title)
         event = Event.query.filter_by(title=seed["title"]).first()

         if not event:
            genre_names = normalise_unique(seed.get("genres", []))
            artist_names = normalise_unique(seed.get("artists", []))
            event_type_name = (seed.get("type") or "").strip()

            event = Event(
               title=seed["title"],
               status=seed["status"],
               date=seed["date"],
               description=seed["description"],
               start_time=seed["start_time"],
               end_time=seed["end_time"],
               image=seed["image"],
               user=user,
               venue=venue,
               event_type=get_or_create_type(event_type_name),
               genres=[get_or_create_genres(n) for n in genre_names],
               artists=[get_or_create_artists(n) for n in artist_names]
            )

            # attach tickets
            event.tickets = [
               Ticket(ticketTier=t["tier"], price=float(t["price"]), perks=t["perks"], availability=int(t["qty"]))
               for t in seed["tickets"]
               if (t.get("tier") or "").strip()
            ]

            db.session.add(event)
            db.session.flush()

            # Seed sample orders for selected events
            tickets_by_tier = {ticket.ticketTier: ticket for ticket in event.tickets}
            seed_sample_orders(event, tickets_by_tier)

            # Attach sample comments for the first three seeded events
            sample_comments = comment_batches.get(event.title)
            if sample_comments and not event.comments:
               base_time = datetime.now()
               for offset, content in enumerate(sample_comments):
                  comment = Comment(
                     content=content,
                     commentDateTime=base_time - timedelta(minutes=15 * offset),
                     user=user,
                     event=event
                  )
                  db.session.add(comment)

         else:
            # ? This block could be changed to fill in missing data for seeded events
            # to be more defensive
            print(f"{event.title} already exists!")

      db.session.commit()        # commit to dbng static images and dummy data provided by Nate