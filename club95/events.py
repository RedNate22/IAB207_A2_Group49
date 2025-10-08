from flask import Blueprint, render_template


events_bp = Blueprint('events_bp', __name__, 'events')

# Event details page
@events_bp.route('/events/eventdetails')
def eventdetails():
    return render_template('events/eventdetails.html')

# Create events page
@events_bp.route('/events/createvent')
def createevent():
    return render_template('events/createevent.html')