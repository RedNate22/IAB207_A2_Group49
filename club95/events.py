from flask import Blueprint, render_template, redirect, url_for, flash
from club95 import db 
from club95.form import EventForm
from .models import Event

events_bp = Blueprint('events_bp', __name__, template_folder='templates')



# Event details page
@events_bp.route('/events/eventdetails')
def eventdetails():
    return render_template('events/eventdetails.html', heading='Event Details')

# Create events page
@events_bp.route('/events/createvent', methods=['GET', 'POST'])
def createevent():
    form = EventForm()
    if form.validate_on_submit():
        
        from . import db

        new_event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            location=form.location.data,
            genre=form.genre.data,
            type=form.type.data,
            status=form.status.data,
            image=form.image.data
        )
        db.session.add(new_event)
        db.session.commit()

        flash("Event created successfully!", "success")
        return redirect(url_for('home_bp.index'))

    return render_template('events/createevent.html' , form=form , heading="Create Event")
