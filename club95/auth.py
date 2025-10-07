## TODO
## Attach instance of login_manager to the app
## Create user_loader callback
## register a seperate "auth" blueprint for authentication routes

from flask import Blueprint, render_template, redirect, url_for, request, flash
from .models import LoginForm, RegisterForm
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user

from . import db


auth_bp = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    # Make the form
    form = RegisterForm()

    # call this line on form post and check for validation against form fields
    if form.validate_on_submit():

        # DID we get form data
        email = form.email.data
        name = form.name.data
        password = form.password.data

        # DOES the user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            #spits you back to register page if user exists already
            return redirect(url_for('auth.register'))
        # create new user with hashed password and add to db
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
        
        # add and commit user to db
        db.session.add(new_user)
        db.session.commit()

        #return success and redirect to login page
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form, heading="Register")

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error=None
    if(form.validate_on_submit()):
        username = form.name.data
        password = form.password.data
        # Find user by email (username) - unsure if I am calling on user right here. need to test
        u1 = User.query.filter_by(name=username).first()

        # if no user exist
        if u1 is None:
            error = 'Incorrect username.'
            flash(error)
            return redirect(url_for('auth.login')) # reload login page if error
        # Check the password
        elif not check_password_hash(u1.password, password):
            error = 'Incorrect password.'
            flash(error)
            return redirect(url_for('auth.login')) # reload login page if error
        if error is None:
            # this logs in the user for the session
            login_user(u1)
            flash('Logged in successfully.')
            # redirect to the next page if it exists otherwise to the index page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home.index'))
        ## Literally no idea how we would get here with all the checks above but you never know
        else:
            print(error)
            flash(error)
    ## passed the gaunlets of checks and logged in
    return render_template('auth/login.html', form=form, heading="Login")

## logout route - logs out user and redirects to homepage. thats it. thats all this does.
@auth_bp.route('auth/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    ## spits user back to homepage
    return redirect(url_for('home.index'))
    