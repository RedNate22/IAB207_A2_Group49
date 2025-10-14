from flask import Blueprint, render_template

from club95.form import UpdateProfileForm

user_bp = Blueprint('user_bp', __name__, template_folder='templates')

# My tickets page
@user_bp.route('/user/mytickets')
def mytickets():
    return render_template('user/mytickets.html', heading='My Tickets')

# ! NOT IMPLEMENTED
# User profile page
#
@user_bp.route('/user/profile')
def profile():
    form = UpdateProfileForm()
    return render_template('user/user.html', form=form)
