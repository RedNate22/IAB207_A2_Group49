from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from sqlalchemy import func
from urllib.parse import quote_plus
from itertools import zip_longest
from club95 import db
from club95.form import EventForm, AddGenreForm, TicketPurchaseForm, CommentForm
from club95.home import _extract_price
from .models import Event, Genre, Artist, Ticket, Order, OrderTicket, Comment, EventArtist, Venue, EventType
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from datetime import datetime, date

events_bp = Blueprint('events_bp', __name__, template_folder='templates')


def _build_map_embed_url(address: str) -> str:
    ## Return a Google Maps embed URL for a provided address string.
    cleaned = (address or '').strip()
    if not cleaned:
        return ''
    query = quote_plus(cleaned)
    return f"https://www.google.com/maps?q={query}&output=embed"


def _get_or_create_venue(address: str):
    ## Fetch an existing venue or create a new one for the supplied address.
    cleaned = (address or '').strip()
    if not cleaned:
        return None
    # Check if the venue already exists
    venue = Venue.query.filter(func.lower(Venue.location) == cleaned.lower()).first()
    embed_url = _build_map_embed_url(cleaned)
    # Create a new venue if not found
    if not venue:
        venue = Venue(location=cleaned, venueMap=embed_url)
        db.session.add(venue)
        db.session.flush()
        # else if venue exists but has no map, update it
    elif not venue.venueMap and embed_url:
        venue.venueMap = embed_url
    # return a venue object
    return venue

# Event details page
@events_bp.route('/events/eventdetails/<int:event_id>', methods=['GET'])
def eventdetails(event_id):
    event = Event.query.get_or_404(event_id)
    purchase_form = TicketPurchaseForm(event.tickets)
    comment_form = CommentForm()
    comments = Comment.query.filter_by(event_id=event.id).order_by(Comment.commentDateTime.desc()).all()

    return render_template(
        'events/eventdetails.html',
        event = event,
        purchase_form = purchase_form,
        comment_form = comment_form,
        comments = comments,
        heading = 'Event Details'
    )


@events_bp.route('/events/myevents', methods=['GET'])
@login_required
def myevents():
    """List only the events created by the logged-in user."""
    term = (request.args.get('search') or '').strip()

    query = f"%{term}%"
    price_value = _extract_price(term)

    filters = [
        Event.title.ilike(query),
        Event.genres.any(Genre.genreType.ilike(query)),
        Event.venue.has(Venue.location.ilike(query)),
        Event.description.ilike(query),
        Event.artists.any(Artist.artistName.ilike(query)),
        Event.date.ilike(query)
    ]

    if price_value is not None:
        min_price_ids = (
            db.select(Ticket.event_id)
            .group_by(Ticket.event_id)
            .having(func.min(Ticket.price) == price_value)
        )
        filters.append(Event.id.in_(min_price_ids))

    events = db.session.scalars(
        db.select(Event)
        .where(Event.user_id == current_user.id)
        .where(db.or_(*filters))
    ).all()

    genre_options = Genre.query.all()
    event_type_options = EventType.query.order_by(EventType.typeName).all()

    return render_template(
        'events/myevents.html',
        heading='My Events',
        events=events,
        search_term=term,
        genre_options=genre_options,
        event_type_options=event_type_options,
    )

# Update event endpoint

@events_bp.route('/events/<int:event_id>/update', methods=['POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.user_id != current_user.id:
        flash('You can only update events you created.', 'warning')
        return redirect(url_for('events_bp.myevents'))

    title = (request.form.get('title') or '').strip()
    event_type_raw = (request.form.get('type') or '').strip()
    status = (request.form.get('status') or '').strip()
    date_value = (request.form.get('date') or '').strip()
    start_time = (request.form.get('start_time') or '').strip()
    end_time = (request.form.get('end_time') or '').strip()
    location = (request.form.get('location') or '').strip()
    description = (request.form.get('description') or '').strip()
    submitted_genre_ids = request.form.getlist('genres')

    if not title:
        flash('Title is required to update an event.', 'warning')
        return redirect(url_for('events_bp.myevents'))

    event.title = title

    selected_event_type = None
    if event_type_raw:
        try:
            event_type_id = int(event_type_raw)
        except ValueError:
            flash('Please select a valid event type.', 'warning')
            return redirect(url_for('events_bp.myevents'))

        selected_event_type = EventType.query.get(event_type_id)
        if not selected_event_type:
            flash('Selected event type does not exist.', 'warning')
            return redirect(url_for('events_bp.myevents'))

    event.event_type = selected_event_type
    if status:
        event.status = status
    if date_value:
        event.date = date_value
    if start_time:
        event.start_time = start_time
    else:
        event.start_time = None
    if end_time:
        event.end_time = end_time
    else:
        event.end_time = None
    event.description = description or None

    image_file = request.files.get('image')
    if image_file and image_file.filename:
        image_filename = secure_filename(image_file.filename)
        if image_filename:
            timestamp = int(datetime.utcnow().timestamp())
            unique_filename = f"event_{event_id}_{timestamp}_{image_filename}"
            image_path = os.path.join('club95', 'static', 'img', unique_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)
            event.image = unique_filename

    if location:
        event.venue = _get_or_create_venue(location)
    else:
        event.venue = None

    if submitted_genre_ids is not None:
        cleaned_ids = []
        for raw_id in submitted_genre_ids:
            raw_id = (raw_id or '').strip()
            if not raw_id:
                continue
            try:
                cleaned_ids.append(int(raw_id))
            except ValueError:
                continue

        if cleaned_ids:
            updated_genres = Genre.query.filter(Genre.id.in_(cleaned_ids)).all()
            event.genres = updated_genres
        else:
            event.genres = []

    db.session.commit()
    flash('Event updated successfully.', 'success')
    return redirect(url_for('events_bp.myevents'))


@events_bp.route('/events/genres', methods=['POST'])
@login_required
def create_genre():
    payload = request.get_json(silent=True) or {}
    genre_name = (payload.get('name') or '').strip()

    if not genre_name:
        return jsonify(success=False, message='Please provide a genre name.'), 400

    existing_genre = Genre.query.filter_by(genreType=genre_name).first()
    if existing_genre:
        return jsonify(success=True, id=existing_genre.id, name=existing_genre.genreType, created=False)

    new_genre = Genre(genreType=genre_name)
    db.session.add(new_genre)
    db.session.commit()

    return jsonify(success=True, id=new_genre.id, name=new_genre.genreType, created=True)

# Create events page
@events_bp.route('/events/createvent', methods=['GET', 'POST'])
@login_required
def createevent():
    # Build the two forms for this page
    form = EventForm()
    add_genre_form = AddGenreForm()

    # prevent selecting past dates on the picker
    today_iso = date.today().isoformat()
    form.date.render_kw = dict(form.date.render_kw or {}, min=today_iso)
    min_date = form.date.render_kw.get('min', today_iso)

    # Fill the Genres multiselect with real options from the database
    form.genres.choices = [(g.id, g.genreType) for g in Genre.query.all()]
    event_type_choices = [(et.id, et.typeName) for et in EventType.query.order_by(EventType.typeName).all()]
    form.type.choices = event_type_choices

    # Preselect genres passed via query string (e.g. after adding a new genre)
    if request.method == 'GET':
        preselected = request.args.get('selected_genres')
        if preselected:
            selected_ids = []
            for raw in preselected.split(','):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    value = int(raw)
                except ValueError:
                    continue
                selected_ids.append(value)
            if selected_ids:
                form.genres.data = selected_ids

    # If the user is logged in and the hidden creator field is empty, prefill it
    if current_user.is_authenticated and not form.user_id.data:
        form.user_id.data = str(current_user.id)

    artist_errors = []

    if form.validate_on_submit():
        # Save the uploaded image (if any) into static/img and keep just the filename in the DB
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join('club95', 'static', 'img', image_filename)
            image_file.save(image_path)

        # Turn selected genre IDs back into Genre objects
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()

        # Collect artist names and set times from repeated inputs
        artist_names = request.form.getlist('artist_name[]')
        artist_times = request.form.getlist('artist_set_time[]')
        artist_errors = []
        artist_entries = []
        seen_artist_names = set()

        for index, raw_name in enumerate(artist_names):
            name = (raw_name or '').strip()
            time_raw = artist_times[index] if index < len(artist_times) else ''
            time_value = (time_raw or '').strip()

            if not name and not time_value:
                continue
            if not name:
                artist_errors.append(f"Artist row {index + 1}: please provide an artist name.")
                continue

            normalized_time = None
            if time_value:
                try:
                    normalized_time = datetime.strptime(time_value, "%H:%M").strftime("%H:%M")
                except ValueError:
                    artist_errors.append(f"Artist '{name}' row {index + 1}: set time must use 24hr format hh:mm.")
                    continue

            normalized_lookup = name.lower()
            if normalized_lookup in seen_artist_names:
                artist_errors.append(f"Artist '{name}' is listed more than once. Remove duplicates.")
                continue
            seen_artist_names.add(normalized_lookup)

            artist_entries.append((name, normalized_time))

        if artist_errors:
            for message in artist_errors:
                flash(message, "danger")
        else:
            artist_links = []
            for name, normalized_time in artist_entries:
                artist_obj = Artist.query.filter_by(artistName=name).first()
                if not artist_obj:
                    artist_obj = Artist(artistName=name)
                    db.session.add(artist_obj)
                    db.session.flush()
                artist_links.append(EventArtist(artist=artist_obj, set_time=normalized_time))

            # Create the Event row from form fields
            selected_event_type = None
            if form.type.data:
                selected_event_type = EventType.query.get(form.type.data)
                if not selected_event_type:
                    flash("Selected event type is invalid.", "danger")
                    return redirect(url_for('events_bp.createevent'))

            new_event = Event(
                title=form.title.data,
                status='OPEN',
                date=form.date.data.strftime('%Y-%m-%d') if form.date.data else None,
                description=form.description.data,
                start_time=form.start_time.data.strftime('%H:%M') if form.start_time.data else None,
                end_time=form.end_time.data.strftime('%H:%M') if form.end_time.data else None,
                image=image_filename,
            )

            venue_record = _get_or_create_venue(form.location.data)
            if venue_record:
                new_event.venue = venue_record

            if selected_event_type:
                new_event.event_type = selected_event_type

            # Link the creator if the hidden field was present
            if form.user_id.data:
                try:
                    new_event.user_id = int(form.user_id.data)
                except ValueError:
                    pass

            # Attach relationships and stage the event for insert
            new_event.genres = selected_genres
            new_event.artist_links = artist_links
            db.session.add(new_event)

            # We need the event id before creating tickets, so flush the INSERT
            db.session.flush()

            # Build tickets from the three parallel arrays in the form
            tier_names = request.form.getlist('ticket_tier[]')
            tier_prices = request.form.getlist('ticket_price[]')
            tier_quantities = request.form.getlist('ticket_quantity[]')
            tier_perks = request.form.getlist('ticket_perks[]')

            # Collect problems and valid ticket data before saving anything
            ticket_errors = []
            pending_tickets = []
            # Walk each tier row from the form so we can validate its fields
            for tname, pstr, qstr, perks_raw in zip_longest(tier_names, tier_prices, tier_quantities, tier_perks, fillvalue=''):
                name_value = (tname or '').strip()
                # Skip rows where the tier name was left empty
                if not name_value:
                    continue
                perks_value = (perks_raw or '').strip()
                # Ensure the price input can be read as a decimal number
                try:
                    price_value = float(pstr)
                except (TypeError, ValueError):
                    ticket_errors.append(f"Ticket price for tier '{name_value}' must be a number.")
                    continue
                # Ensure the quantity input can be read as a whole number
                try:
                    qty_value = int(qstr)
                except (TypeError, ValueError):
                    ticket_errors.append(f"Ticket quantity for tier '{name_value}' must be a whole number.")
                    continue
                # Track whether this row needs to be rejected after deeper checks
                invalid_entry = False
                # Reject negative prices
                if price_value < 0:
                    ticket_errors.append(f"Ticket price for tier '{name_value}' cannot be negative.")
                    invalid_entry = True
                # Reject zero or negative quantities
                if qty_value < 1:
                    ticket_errors.append(f"Ticket quantity for tier '{name_value}' must be at least 1.")
                    invalid_entry = True
                if perks_value and len(perks_value) > 50:
                    ticket_errors.append(f"Ticket perks for tier '{name_value}' must be 50 characters or fewer.")
                    invalid_entry = True
                # Only queue valid rows for insertion
                if not invalid_entry:
                    pending_tickets.append((name_value, price_value, qty_value, perks_value or None))

            # If anything failed validation, abort and let the user know what to fix
            # Likely won't reach here due to input constraints, but just in case
            if ticket_errors:
                db.session.rollback()
                for message in ticket_errors:
                    flash(message, "danger")
                return redirect(url_for('events_bp.createevent'))

            # Persist every validated ticket tier for the new event
            for name_value, price_value, qty_value, perks_value in pending_tickets:
                ticket = Ticket(
                    ticketTier=name_value,
                    price=price_value,
                    availability=qty_value,
                    perks=perks_value,
                    event_id=new_event.id
                )
                db.session.add(ticket)

            # Finalise the whole transaction: event, any new artists, and tickets
            db.session.commit()

            flash("Event created successfully!", "success")
            # Send the user to the event details page for this new event
            return redirect(url_for('events_bp.eventdetails', event_id=new_event.id))

    # If it was a POST but invalid, surface per-field validation messages
    if request.method == 'POST':
        for field_name, errors in form.errors.items():
            field_label = getattr(getattr(form, field_name), 'label', None)
            label_text = field_label.text if field_label else field_name.replace('_', ' ').title()
            for message in errors:
                flash(f"{label_text}: {message}", "danger")

    # First load or invalid POST falls through to re-render the page
    return render_template(
        'events/createevent.html',
        form=form,
        add_genre_form=add_genre_form,
        heading="Create Event",
        artist_errors=artist_errors,
        prefilled_genres=form.genres.data or [],
        min_date=min_date
    )
@events_bp.route('/events/add_genre', methods=['POST'])
@login_required
def add_genre():
    add_genre_form = AddGenreForm()
    if add_genre_form.validate_on_submit():
        new_genre_name = add_genre_form.new_genre.data.strip()
        selected_ids = []
        if add_genre_form.selected_genres.data:
            for raw in add_genre_form.selected_genres.data.split(','):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    value = int(raw)
                except ValueError:
                    continue
                selected_ids.append(value)
        if not Genre.query.filter_by(genreType=new_genre_name).first():
            new_genre = Genre(genreType=new_genre_name)
            db.session.add(new_genre)
            db.session.commit()
            selected_ids.append(new_genre.id)
            flash(f"Genre '{new_genre_name}' added.", "success")
        else:
            flash(f"Genre '{new_genre_name}' already exists.", "info")
        if selected_ids:
            valid_ids = []
            for gid in selected_ids:
                if Genre.query.get(gid) and gid not in valid_ids:
                    valid_ids.append(gid)
            if valid_ids:
                selected_param = ','.join(str(gid) for gid in valid_ids)
                return redirect(url_for('events_bp.createevent', selected_genres=selected_param))
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
    # Lookup event by ID, if not found: return 404
    event = Event.query.get_or_404(event_id)
    form = TicketPurchaseForm(event.tickets, formdata = request.form)

    # If form is invalid, redirect back with error message
    # Validation is checked by WTForms
    if not form.validate_on_submit():
        flash("Please review your ticket selections.", "danger")
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))

    # Clears both order items and total amount to start fresh when opening modal
    order_items = []
    total_amount = 0.0

    # Iterate through tickets and get quantities from form
    for ticket in event.tickets:
        field = getattr(form, f"quantity_{ticket.id}", None)
        # If 'field' exists, use it's 'data' attribute, otherwise default to 0
        quantity = field.data if field is not None else 0 
        # If 'quantity' is falsy (None, 0, '', etc.), replace with 0
        quantity = quantity or 0

        # Negative quantity entered
        if quantity < 0:
            flash("Quantities cannot be negative.", "danger")
            return redirect(url_for('events_bp.eventdetails', event_id = event.id))

        # No quantity entered
        # Prevents forcing user to buy one of every ticket type
        if quantity == 0:
            continue

        # Not enough tickets available for quantity entered
        if quantity > ticket.availability:
            flash(f"Not enough availability for {ticket.ticketTier}. Only {ticket.availability} left.",
                "warning")
            return redirect(url_for('events_bp.eventdetails', event_id = event.id))
        
        # Add ticket and quantity to order items and update total amount
        order_items.append((ticket, quantity))
        total_amount += ticket.price * quantity

    # If no tickets were selected, flash error and redirect
    if not order_items:
        flash("Select at least one ticket to purchase.", "warning")
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))

    # Create order and order tickets table items, update ticket availability
    # to reflect this on  next visit to same modal
    order = Order(
        # ! utcnow is deprecated
        order_date = datetime.utcnow(),  # * previously datetime.utcnow() but was deprecated
        amount = total_amount,
        user_id = current_user.id
    )

    # Add order object to database
    db.session.add(order)
    db.session.flush()

    # Create OrderTicket entries and update ticket availability
    # for each ticket in order_items, create an OrderTicket entry and update ticket availability
    for ticket, quantity in order_items:
        db.session.add(
            OrderTicket(
                order_id = order.id,
                ticket_id = ticket.id,
                quantity = quantity,
                price_at_purchase = ticket.price
            )
        )
        # Update ticket availability
        ticket.availability -= quantity

    # Commit all changes to database
    db.session.commit()
    # Confirm successful purchase
    flash("Tickets purchased successfully!", "success")
    # Return to event details page
    return redirect(url_for('events_bp.eventdetails', event_id = event.id))