# import flask - from 'package' import 'Class'
from flask import Flask, session 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# create a db object that is an instance of SQLAlchemy class
db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
   app = Flask(__name__)  # this is the name of the module/package that is calling this app
   # Should be set to false in a production environment
   app.debug = True
   app.secret_key = 'somesecretkey'

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

   # set the app configuration data - where the db is located "provider://location.name"
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
   # initialise db with flask app
   db.init_app(app)

   Bootstrap5(app)

   db.Model.metadata.clear()
   
   # ! NOT IMPLEMENTED YET
   # initialise the login manager
   login_manager = LoginManager()
   
   # ! NOT IMPLEMENTED YET
   # set the name of the login function that lets user login
   # in our case it is auth.login (blueprintname.viewfunction name)
   # redirect to login page if user tries to access a login_required page without being logged in
   login_manager.login_view = 'auth_bp.login'
   login_manager.init_app(app)

   # ! NOT IMPLEMENTED YET - Thank you Nate for doing this step already - B
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
   
   return app