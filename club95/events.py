from flask import Blueprint, render_template
from club95 import db 

events_bp = Blueprint('events_bp', __name__, 'events')

#Event model
class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Event {self.title}>"

# Event details page
@events_bp.route('/events/eventdetails')
def eventdetails():
    return render_template('events/eventdetails.html')

# Create events page
@events_bp.route('/events/createvent')
def createevent():
    return render_template('events/createevent.html')