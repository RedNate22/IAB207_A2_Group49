from flask import Blueprint, render_template, redirect, url_for, flash, request
from club95 import db 
from club95.form import EventForm, AddGenreForm, TicketPurchaseForm, CommentForm
from .models import Event
from . import db
import os
from werkzeug.utils import secure_filename
from .models import Genre, Artist, Ticket, Order, OrderTicket, Comment
from flask_login import current_user, login_required
from datetime import datetime

events_bp = Blueprint('events_bp', __name__, template_folder='templates')



# Event details page
@events_bp.route('/events/eventdetails')
def eventdetails():
    return render_template('events/eventdetails.html', heading='Event Details')

# Create events page
@events_bp.route('/events/createvent', methods=['GET', 'POST'])
def createevent():
    
    # Set choices for genres and artists
    form = EventForm()
    add_genre_form = AddGenreForm()
    form.genres.choices = [(g.id, g.genreType) for g in Genre.query.all()]
    form.artists.choices = [(a.id, a.artistName) for a in Artist.query.all()]

    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join('club95', 'static', 'img', image_filename)
            image_file.save(image_path)

        # Get selected genres and artists
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        selected_artists = Artist.query.filter(Artist.id.in_(form.artists.data)).all()

        new_event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            location=form.location.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            type=form.type.data,
            status=form.status.data,
            image=image_filename
        )
        new_event.genres = selected_genres
        new_event.artists = selected_artists
        db.session.add(new_event)
        db.session.commit()

        flash("Event created successfully!", "success")
        return redirect(url_for('home_bp.index'))

    return render_template('events/createevent.html', form=form, add_genre_form=add_genre_form, heading="Create Event")

@events_bp.route('/events/add_genre', methods=['POST'])
def add_genre():
    add_genre_form = AddGenreForm()
    if add_genre_form.validate_on_submit():
        new_genre_name = add_genre_form.new_genre.data.strip()
        if not Genre.query.filter_by(genreType=new_genre_name).first():
            new_genre = Genre(genreType=new_genre_name)
            db.session.add(new_genre)
            db.session.commit()
            flash(f"Genre '{new_genre_name}' added.", "success")
        else:
            flash(f"Genre '{new_genre_name}' already exists.", "info")
    else:
        flash("Please provide a valid genre name.", "warning")
    return redirect(url_for('events_bp.createevent'))


# Comment creation endpoint
@events_bp.route('/events/eventdetails/<int:event_id>/comment', methods=['POST'])
@login_required
def add_comment(event_id):
    event = Event.query.get_or_404(event_id)
    form = CommentForm()

    if not form.validate_on_submit():
        message = form.content.errors[0] if form.content.errors else "Comment cannot be empty."
        flash(message, "warning")
        return redirect(url_for('events_bp.eventdetails', event_id=event.id))

    content = form.content.data.strip()
    if not content:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for('events_bp.eventdetails', event_id=event.id))

    new_comment = Comment(
        content=content,
        commentDateTime=datetime.today(),
        event_id=event.id,
        user_id=current_user.id
    )

    # Adds comment to Database
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment posted successfully!", "success")
    return redirect(url_for('events_bp.eventdetails', event_id=event.id))

# Purchase tickets
@events_bp.route('/events/purchase/<int:event_id>', methods = ['POST'])
@login_required
def purchase_tickets(event_id):
    event = Event.query.get_or_404(event_id)
    form = TicketPurchaseForm(event.tickets, formdata = request.form)

    if not form.validate_on_submit():
        flash("Please review your ticket selections.", "danger")
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))

    order_items = []
    total_amount = 0.0

    for ticket in event.tickets:
        field = getattr(form, f"quantity_{ticket.id}", None)
        quantity = field.data if field is not None else 0
        quantity = quantity or 0

        # Negative quantity entered
        if quantity < 0:
            flash("Quantities cannot be negative.", "danger")
            return redirect(url_for('events_bp.eventdetails', event_id = event.id))

        # No quantity entered
        if quantity == 0:
            continue
            # ? put it here?
            # flash("Select at least one ticket to purchase.", "warning")
            # return redirect(url_for('events_bp.eventdetails', event_id = event.id))

        # Not enough tickets
        if quantity > ticket.availability:
            flash(f"Not enough availability for {ticket.ticketTier}. Only {ticket.availability} left.",
                "warning")
            return redirect(url_for('events_bp.eventdetails', event_id = event.id))
        
        order_items.append((ticket, quantity))
        total_amount += ticket.price * quantity

        # ? put it under quantity == 0?
        if not order_items:
            flash("Select at least one ticket to purchase.", "warning")
            return redirect(url_for('events_bp.eventdetails', event_id = event.id))

        order = Order(
            # ! utcnow is deprecated
            order_data = datetime.utcnow(),
            amount = total_amount,
            user_id = current_user.id
        )

        db.session.add(order)
        db.session.flush()

        for ticket, quantity in order_items:
            db.session.add(
                OrderTicket(
                    order_id = order.id,
                    ticket_id = ticket.id,
                    quantity = quantity,
                    price_at_purchase = ticket.price
                )
            )

            ticket.availability -= quantity

        db.session.commit()
        flash("Tickets purchased successfully!", "success")
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))
        

                