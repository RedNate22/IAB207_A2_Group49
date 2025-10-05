from flask import  render_template
from . import events_bp

# Event details page
@events_bp.route('/events/eventdetails')
def eventdetails():
    return render_template('eventdetails.html')

# Create events page
@events_bp.route('/events/createvent')
def createevent():
    return render_template('createevent.html')