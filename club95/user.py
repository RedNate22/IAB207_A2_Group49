from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from club95.form import UpdateProfileForm
from .models import Order, OrderTicket,Ticket

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
# ! NOT IMPLEMENTED
# User profile page
#
@user_bp.route('/user/profile')
def profile():
    form = UpdateProfileForm()
    return render_template('user/user.html', form=form)
