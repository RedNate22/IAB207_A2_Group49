import os

from flask import Blueprint, render_template, redirect, url_for, request, flash
from .form import LoginForm, RegisterForm
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
        streetAddress = form.streetAddress.data
        bio = form.bio.data
        profile_picture_file = form.profilePicture.data
        profile_picture_path = None
        if profile_picture_file and getattr(profile_picture_file, 'filename', ''):
            filename = secure_filename(profile_picture_file.filename)
            if filename:
                upload_dir = os.path.join('club95', 'static', 'img')
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, filename)
                profile_picture_file.save(save_path)
                profile_picture_path = os.path.join('img', filename).replace('\\', '/')

        # DOES the user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'registration_email_error')
            return redirect(url_for('auth_bp.register'))
        # create new user with hashed password and add to db
        new_user = User(
            email=email,
            firstName=firstName,
            lastName=lastName,
            password=generate_password_hash(password, method='scrypt', salt_length=16),
            phoneNumber=phonenumber,
            bio=bio,
            streetAddress=streetAddress,
            profilePicture=profile_picture_path
        )
        db.session.add(new_user)
        db.session.commit()

        #return success and redirect to login page
        flash('Registration successful! Please log in.', 'registration_success')
        return redirect(url_for('auth_bp.login'))
    
    return render_template('/auth/register.html', form=form, heading="Register")

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # Find user by email
        u1 = User.query.filter_by(email=email).first()

        if u1 is None:
            error = 'Incorrect email.'
            flash(error, 'login_error')
            return redirect(url_for('auth_bp.login'))
        elif not check_password_hash(u1.password, password):
            error = 'Incorrect password.'
            flash(error, 'login_error')
            return redirect(url_for('auth_bp.login'))
        if error is None:
            login_user(u1)
            flash('Logged in successfully. Welcome back, ' + u1.firstName + '!', 'login_success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home_bp.index'))
        else:
            print(error)
            flash(error, 'login_error')
    ## passed the gaunlets of checks and logged in
    return render_template('/auth/login.html', form=form, heading="Login")

## logout route - logs out user and redirects to homepage. thats it. thats all this does.
@auth_bp.route('/auth/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'logout-success')
    ## spits user back to homepage
    return redirect(url_for('home_bp.index'))
    