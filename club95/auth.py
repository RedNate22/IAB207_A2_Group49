## TODO
## Attach instance of login_manager to the app
## Create user_loader callback
## register a seperate "auth" blueprint for authentication routes

from flask import Blueprint, render_template, redirect, url_for, request, flash
from .form import LoginForm, RegisterForm
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user

from . import db


auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')

@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    # Make the form
    form = RegisterForm()

    # call this line on form post and check for validation against form fields
    if form.validate_on_submit():

        # DID we get form data
        email = form.email.data
        firstName = form.firstName.data
        lastName = form.lastName.data
        password = form.password.data
        phonenumber = form.phonenumber.data
        bio = form.bio.data
        profilePicture = form.profilePicture.data

        # DOES the user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('auth_bp.register'))
        # create new user with hashed password and add to db
        new_user = User(
            email=email,
            firstName=firstName,
            lastName=lastName,
            password=generate_password_hash(password, method='scrypt', salt_length=16),
            phoneNumber=phonenumber,
            bio=bio,
            profilePicture=profilePicture
        )
        db.session.add(new_user)
        db.session.commit()

        #return success and redirect to login page
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth_bp.login'))
    
    return render_template('/auth/register.html', form=form, heading="Register")

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        firstName = form.firstName.data
        password = form.password.data
        # Find user by firstName
        u1 = User.query.filter_by(firstName=firstName).first()

        if u1 is None:
            error = 'Incorrect first name.'
            flash(error)
            return redirect(url_for('auth_bp.login'))
        elif not check_password_hash(u1.password, password):
            error = 'Incorrect password.'
            flash(error)
            return redirect(url_for('auth_bp.login'))
        if error is None:
            login_user(u1)
            flash('Logged in successfully.')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home_bp.index'))
        else:
            print(error)
            flash(error)
    ## passed the gaunlets of checks and logged in
    return render_template('/auth/login.html', form=form, heading="Login")

## logout route - logs out user and redirects to homepage. thats it. thats all this does.
@auth_bp.route('/auth/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    ## spits user back to homepage
    return redirect(url_for('home_bp.index'))
    