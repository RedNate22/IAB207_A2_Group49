from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from sqlalchemy import func, or_
from urllib.parse import quote_plus
from itertools import zip_longest
from club95 import db
from club95.form import EventForm, AddGenreForm, TicketPurchaseForm, CommentForm
from club95.home import _extract_price
from .models import Event, Genre, Artist, Ticket, Order, OrderTicket, Comment, EventArtist, Venue, EventType, EventImage
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from datetime import datetime, date, timezone

events_bp = Blueprint('events_bp', __name__, template_folder='templates')

# helper to build Google Maps embed URL
def _build_map_embed_url(address: str) -> str:
    ## Return a Google Maps embed URL for a provided address string.
    cleaned = (address or '').strip()
    if not cleaned:
        return ''
    query = quote_plus(cleaned)
    return f"https://www.google.com/maps?q={query}&output=embed"

# Helper to get or create a Venue record
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

# Helper to save additional event media files
def _save_event_media(event, file_storage_list):
    # Persist additional media uploads for a given event
    if not event or not file_storage_list:
        return

    # set the save folder
    media_folder = os.path.join('club95', 'static', 'img', 'event_media')
    os.makedirs(media_folder, exist_ok=True)

    # Get the next order index for the event images
    current_max = db.session.query(func.max(EventImage.order_index)).filter_by(event_id=event.id).scalar()
    next_index = (current_max or 0) + 1
    # Generate a timestamp for unique file naming, so we don't overwrite files
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    # Save each file
    for storage in file_storage_list:
        # Skip empty uploads
        if not storage or not storage.filename:
            continue
        # Secure the filename
        safe_name = secure_filename(storage.filename)
        if not safe_name:
            continue
        # Create a unique filename
        unique_name = f"event_{event.id}_{timestamp}_{next_index}_{safe_name}"
        destination = os.path.join(media_folder, unique_name)
        storage.save(destination)

        db.session.add(EventImage(
            event_id=event.id,
            filename=f"event_media/{unique_name}",
            order_index=next_index
        ))
        # Increment the order index for the next file
        next_index += 1


def _sync_event_status(event: Event) -> None:
    # Automatically shift event status based on ticket pool and schedule
    if not event:
        return

    today = date.today()

    event_date = None
    if event.date:
        try:
            event_date = datetime.strptime(event.date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            event_date = None

    current_status = (event.status or '').strip().upper()

    if event_date and event_date < today:
        if current_status != 'INACTIVE':
            event.status = 'INACTIVE'
        return

    total_remaining = sum(max(0, (ticket.availability or 0)) for ticket in event.tickets)

    if current_status == 'CANCELLED':
        return

    if total_remaining <= 0:
        if current_status != 'SOLD OUT':
            event.status = 'SOLD OUT'
    elif current_status == 'SOLD OUT':
        event.status = 'OPEN'

# Event details page
@events_bp.route('/events/eventdetails/<int:event_id>', methods=['GET'])
def eventdetails(event_id):
    event = Event.query.get_or_404(event_id)
    original_status = event.status
    _sync_event_status(event)
    if event.status != original_status:
        db.session.commit()
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
    # Display and filter events created by the logged-in user.

    term = (request.args.get('search') or '').strip()

    # Helper to read many possible keys (handles [] and non-[] names)
    def _get_multi(*keys):
        vals = []
        for k in keys:
            vals += request.args.getlist(k)
        # fall back to single-value params if someone used them
        for k in keys:
            v = request.args.get(k)
            if v:
                vals.append(v)
        # clean
        out = []
        for v in vals:
            v = (v or '').strip()
            if v:
                out.append(v)
        return out

    # Read filters no matter how the frontend named them
    et_raw = _get_multi('event_type[]', 'event_type', 'type[]', 'type')
    g_raw  = _get_multi('genre[]', 'genre', 'genres[]', 'genres')
    st_raw = _get_multi('status[]', 'status', 'statuses[]', 'statuses')

    # Split values into ids vs names for types/genres
    def split_ids_names(items):
        ids, names = [], []
        for v in items:
            if v.isdigit():
                ids.append(int(v))
            else:
                names.append(v)
        return ids, names

    et_ids, et_names = split_ids_names(et_raw)
    g_ids,  g_names  = split_ids_names(g_raw)
    # Normalise statuses to upper for DB comparison; also keep originals for ilike fallback
    st_norm = [s.upper() for s in st_raw]

    # Base query: only the current user's events
    q = db.select(Event).where(Event.user_id == current_user.id)

    # Keyword search across several fields
    if term:
        like = f"%{term}%"
        q = q.where(or_(
            Event.title.ilike(like),
            Event.description.ilike(like),
            Event.date.ilike(like),
            Event.venue.has(Venue.location.ilike(like)),
            Event.genres.any(Genre.genreType.ilike(like)),
            Event.artists.any(Artist.artistName.ilike(like))
        ))

    # Event Type filters (by id OR by name, name is case-insensitive)
    if et_ids:
        q = q.where(Event.event_type.has(EventType.id.in_(et_ids)))
    if et_names:
        # use ilike to be resilient to case/spacing
        ors = [Event.event_type.has(EventType.typeName.ilike(n)) for n in et_names]
        q = q.where(or_(*ors))

    # Genre filters (by id OR by name)
    if g_ids:
        q = q.where(Event.genres.any(Genre.id.in_(g_ids)))
    if g_names:
        ors = [Event.genres.any(Genre.genreType.ilike(n)) for n in g_names]
        q = q.where(or_(*ors))

    # Status filters (try exact uppercase; if that yields nothing, ilike fallback)
    if st_norm:
        q = q.where(or_(
            Event.status.in_(st_norm),
            # fallback: any of the raw values via ilike, in case labels differ
            *[Event.status.ilike(s) for s in st_raw]
        ))

    # Order newest first; if date is stored as text it will still be stable enough for now
    events = db.session.scalars(q.order_by(Event.date.desc())).all()

    status_changed = False
    for event in events:
        original_status = event.status
        _sync_event_status(event)
        if event.status != original_status:
            status_changed = True

    if status_changed:
        db.session.commit()

    if not events:
        flash('No events matched your filters. Try a different search term or filter.', 'search_info')

    event_type_options = EventType.query.order_by(EventType.typeName).all()
    genre_options = Genre.query.order_by(Genre.genreType).all()

    return render_template(
        'events/myevents.html',
        heading='My Events',
        events=events,
        search_term=term,
        event_type_options=event_type_options,
        genre_options=genre_options
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
            timestamp = int(datetime.now(timezone.utc).timestamp())
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

    # Ticket editor pushes parallel arrays (ids, names, prices, etc.) so grab them up front
    ticket_ids = request.form.getlist('ticket_row_id[]')
    ticket_names = request.form.getlist('ticket_row_name[]')
    ticket_prices = request.form.getlist('ticket_row_price[]')
    ticket_quantities = request.form.getlist('ticket_row_quantity[]')
    ticket_perks_values = request.form.getlist('ticket_row_perks[]')
    ticket_delete_flags = request.form.getlist('ticket_row_delete[]')

    if ticket_ids or ticket_names or ticket_prices or ticket_quantities or ticket_perks_values or ticket_delete_flags:
        # Map existing tickets by id so we can tell updates from new rows in O(1)
        existing_ticket_map = {str(ticket.id): ticket for ticket in event.tickets}
        tickets_to_delete = []
        tickets_to_update = []
        tickets_to_create = []
        ticket_errors = []

        for row_id_raw, name_raw, price_raw, qty_raw, perks_raw, delete_raw in zip_longest(
            ticket_ids,
            ticket_names,
            ticket_prices,
            ticket_quantities,
            ticket_perks_values,
            ticket_delete_flags,
            fillvalue=''
        ):
            row_id = (row_id_raw or '').strip()
            tier_name = (name_raw or '').strip()
            price_input = (price_raw or '').strip()
            quantity_input = (qty_raw or '').strip()
            perks_input = (perks_raw or '').strip()
            delete_requested = (delete_raw or '').strip() == '1'

            # Ignore stray empty rows that the browser may submit
            if not row_id and not tier_name and not price_input and not quantity_input and not perks_input:
                continue

            # Deletion requests are flagged separately so we honour them later
            if delete_requested:
                if row_id:
                    tickets_to_delete.append(row_id)
                continue

            invalid_entry = False
            if not tier_name:
                ticket_errors.append('Ticket tier name cannot be blank.')
                invalid_entry = True

            price_value = None
            quantity_value = None
            # Price needs to be a decimal value we can store as float
            if price_input:
                try:
                    price_value = float(price_input)
                except (TypeError, ValueError):
                    ticket_errors.append(f"Ticket price for tier '{tier_name or 'New Tier'}' must be a valid number.")
                    invalid_entry = True
            else:
                ticket_errors.append(f"Ticket price for tier '{tier_name or 'New Tier'}' must be provided.")
                invalid_entry = True

            # Availability must be a whole number and cannot be skipped
            if quantity_input:
                try:
                    quantity_value = int(quantity_input)
                except (TypeError, ValueError):
                    ticket_errors.append(f"Ticket quantity for tier '{tier_name or 'New Tier'}' must be a whole number.")
                    invalid_entry = True
            else:
                ticket_errors.append(f"Ticket quantity for tier '{tier_name or 'New Tier'}' must be provided.")
                invalid_entry = True

            if not invalid_entry:
                # Guard against nonsense values before we queue an update
                if price_value is not None and price_value < 0:
                    ticket_errors.append(f"Ticket price for tier '{tier_name}' cannot be negative.")
                    invalid_entry = True
                if quantity_value is not None and quantity_value < 0:
                    ticket_errors.append(f"Ticket quantity for tier '{tier_name}' cannot be negative.")
                    invalid_entry = True
                if perks_input and len(perks_input) > 120:
                    ticket_errors.append(f"Ticket perks for tier '{tier_name}' must be 120 characters or fewer.")
                    invalid_entry = True
                if row_id and row_id not in existing_ticket_map:
                    ticket_errors.append('One of the ticket tiers could not be matched to this event.')
                    invalid_entry = True

            if invalid_entry:
                continue

            # Normalise data so we don't double-handle rounding or empty perks
            rounded_price = round(price_value or 0.0, 2)
            normalized_perks = perks_input or None

            if row_id:
                tickets_to_update.append((row_id, tier_name, rounded_price, quantity_value, normalized_perks))
            else:
                tickets_to_create.append((tier_name, rounded_price, quantity_value, normalized_perks))

        if ticket_errors:
            # One bad row spoils the bunch, so roll back and surface everything to the user
            db.session.rollback()
            for message in ticket_errors:
                flash(message, 'danger')
            return redirect(url_for('events_bp.myevents'))

        refunded_tiers = []
        removed_tiers = []
        for row_id in tickets_to_delete:
            ticket_obj = existing_ticket_map.pop(row_id, None)
            if not ticket_obj:
                continue

            refund_total = 0.0
            if ticket_obj.order_links:
                affected_orders = set()
                for order_link in list(ticket_obj.order_links):
                    quantity = order_link.quantity or 0
                    line_refund = (order_link.price_at_purchase or 0.0) * quantity
                    refund_total += line_refund

                    order = order_link.order
                    if order:
                        order.amount = max(0.0, (order.amount or 0.0) - line_refund)
                        affected_orders.add(order)
                        if order_link in order.line_items:
                            order.line_items.remove(order_link)

                    if order_link in ticket_obj.order_links:
                        ticket_obj.order_links.remove(order_link)

                    db.session.delete(order_link)

                for order in affected_orders:
                    if not order.line_items:
                        db.session.delete(order)
                    elif order.amount is None or order.amount < 0:
                        order.amount = 0.0

                refunded_tiers.append((ticket_obj.ticketTier, refund_total))
            else:
                removed_tiers.append(ticket_obj.ticketTier)

            db.session.delete(ticket_obj)

        for row_id, tier_name, price_value, quantity_value, perks_value in tickets_to_update:
            ticket_obj = existing_ticket_map.get(row_id)
            if not ticket_obj:
                continue
            # Straightforward field updates for any tier that survived validation
            ticket_obj.ticketTier = tier_name
            ticket_obj.price = price_value
            ticket_obj.availability = quantity_value
            ticket_obj.perks = perks_value

        for tier_name, price_value, quantity_value, perks_value in tickets_to_create:
            # New tiers are attached to the current event and will be picked up on commit
            db.session.add(Ticket(
                ticketTier=tier_name,
                price=price_value,
                availability=quantity_value,
                perks=perks_value,
                event=event
            ))

        if refunded_tiers:
            refund_summary = ', '.join(
                f"{tier_name} (${refund_amount:.2f})" for tier_name, refund_amount in refunded_tiers
            )
            flash(f'Refunds will be issued for removed ticket tiers: {refund_summary}', 'warning')

        if removed_tiers:
            removed_list = ', '.join(removed_tiers)
            flash(f'Removed ticket tiers: {removed_list}', 'info')

    _sync_event_status(event)

    # Prepare to replace or remove existing carousel media before adding new files
    media_folder = os.path.join('club95', 'static', 'img', 'event_media')

    for media in list(event.images):
        # Replace an existing event media image if the user supplied a new file
        replacement_file = request.files.get(f'replace_image_{media.id}')
        if replacement_file and replacement_file.filename:
            safe_name = secure_filename(replacement_file.filename)
            if safe_name:
                os.makedirs(media_folder, exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                unique_name = f"event_{event.id}_{timestamp}_{media.id}_{safe_name}"
                destination = os.path.join(media_folder, unique_name)
                replacement_file.save(destination)

                if media.filename:
                    # Remove the obsolete file from disk when possible
                    old_path = os.path.join('club95', 'static', 'img', media.filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                media.filename = f"event_media/{unique_name}"

    # Gather any media IDs flagged for deletion from the form submission
    delete_ids_raw = request.form.getlist('delete_media_ids')
    delete_ids = []
    for raw_id in delete_ids_raw:
        try:
            delete_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if delete_ids:
        images_to_delete = EventImage.query.filter(EventImage.event_id == event.id, EventImage.id.in_(delete_ids)).all()
        for media in images_to_delete:
            if media.filename:
                media_path = os.path.join('club95', 'static', 'img', media.filename)
                if os.path.exists(media_path):
                    try:
                        os.remove(media_path)
                    except OSError:
                        pass
            db.session.delete(media)

    additional_media_files = request.files.getlist('additional_media')
    _save_event_media(event, additional_media_files)

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
                if perks_value and len(perks_value) > 120:
                    ticket_errors.append(f"Ticket perks for tier '{name_value}' must be 120 characters or fewer.")
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

            additional_media_files = request.files.getlist('additional_media')
            _save_event_media(new_event, additional_media_files)

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
    event_status = (event.status or '').strip().upper()
    if event_status == 'CANCELLED':
        flash('Ticket sales are closed for this event.', 'warning')
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))
    if event_status == 'SOLD OUT':
        flash('This event is sold out.', 'warning')
        return redirect(url_for('events_bp.eventdetails', event_id = event.id))

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
            flash("Not enough tickets available for your order.", "danger")
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
    order_date = datetime.now(timezone.utc),
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

    _sync_event_status(event)

    # Commit all changes to database
    db.session.commit()
    # Confirm successful purchase
    flash("Tickets purchased successfully!", "success")
    # Redirect to the user's tickets page so they can see the new order
    return redirect(url_for('user_bp.mytickets'))