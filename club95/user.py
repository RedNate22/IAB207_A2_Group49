from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from club95.form import UpdateProfileForm
from .models import Order, OrderTicket, Ticket
from . import db
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user_bp', __name__, template_folder='templates')

# My tickets page
@user_bp.route('/user/mytickets')
@login_required
def mytickets():
    # Fetch the authenticated user's orders
    orders = (
        Order.query
        .options(
            joinedload(Order.line_items)
            .joinedload(OrderTicket.ticket)
            .joinedload(Ticket.event)
        )
        .filter_by(user_id=current_user.id)
        .order_by(Order.order_date.desc())
        .all()
    )
    # Render the My Tickets view with the assembled order history
    return render_template(
        'user/mytickets.html',
        heading='My Tickets',
        orders=orders
    )

# User profile page

@user_bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)
    editing = False
    def populate_form_from_user():
        form.firstName.data = current_user.firstName
        form.lastName.data = current_user.lastName
        form.email.data = current_user.email
        form.phonenumber.data = current_user.phoneNumber
        form.bio.data = current_user.bio
        form.profilePicture.data = current_user.profilePicture
        form.password.data = ''

    if request.method == 'GET':
        populate_form_from_user()
    if request.method == 'POST' and 'edit' in request.form:
        editing = True
        populate_form_from_user()
    elif form.validate_on_submit():
        # Only update fields if provided
        if form.email.data:
            current_user.email = form.email.data
        if form.firstName.data:
            current_user.firstName = form.firstName.data
        if form.lastName.data:
            current_user.lastName = form.lastName.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data, method='scrypt', salt_length=16)
        if form.phonenumber.data:
            current_user.phoneNumber = form.phonenumber.data
        if form.bio.data:
            current_user.bio = form.bio.data
        if form.profilePicture.data:
            current_user.profilePicture = form.profilePicture.data
        db.session.commit()
        db.session.refresh(current_user)
        editing = False
        populate_form_from_user()
    return render_template('user/user.html', form=form, editing=editing, user=current_user)