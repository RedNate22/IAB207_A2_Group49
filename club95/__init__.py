# import flask - from 'package' import 'Class'
from flask import Flask 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
   app = Flask(__name__)  # this is the name of the module/package that is calling this app
   # Should be set to false in a production environment
   app.debug = True
   app.secret_key = 'somesecretkey'
   # set the app configuration data 
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
   # initialise db with flask app
   db.init_app(app)

   Bootstrap5(app)
   
   # ! NOT IMPLEMENTED YET
   # initialise the login manager
   # login_manager = LoginManager()
   
   # ! NOT IMPLEMENTED YET
   # set the name of the login function that lets user login
   # in our case it is auth.login (blueprintname.viewfunction name)
   # login_manager.login_view = 'auth.login'
   # login_manager.init_app(app)

   # ! NOT IMPLEMENTED YET
   # create a user loader function takes userid and returns User
   # Importing inside the create_app function avoids circular references
   # from .models import User
   # @login_manager.user_loader
   # def load_user(user_id):
   #    return db.session.scalar(db.select(User).where(User.id==user_id))

   from .home import home_bp 
   app.register_blueprint(home_bp)

   from .user import user_bp
   app.register_blueprint(user_bp)

   from .events import events_bp
   app.register_blueprint(events_bp)

   # ! not implemented yet 
   # from . import auth
   # app.register_blueprint(auth.auth_bp)
   
   return app