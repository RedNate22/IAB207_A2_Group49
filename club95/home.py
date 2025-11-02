import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from datetime import date, datetime
from .models import Artist, Event, Genre, Ticket, Venue
from . import db

home_bp = Blueprint('home_bp', __name__, template_folder='templates')


def _active_event_clause():
    # Return a SQL clause that excludes inactive events from public browsing.
    return db.or_(Event.status.is_(None), func.upper(Event.status) != 'INACTIVE')

def _parse_event_date(raw_value: str):
    # Attempt to convert a stored event date string into a real date object.
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

def _select_upcoming_events(events, limit=3):
    # Extract the nearest upcoming OPEN events from an iterable of Event objects.
    today = date.today()
    upcoming = []
    # simple sorting
    for ev in events:
        parsed_date = _parse_event_date(ev.date)
        status = (ev.status or '').strip().upper()
        if parsed_date and parsed_date >= today and status == 'OPEN':
            upcoming.append((parsed_date, ev))

    upcoming.sort(key=lambda item: item[0])
    return [ev for _, ev in upcoming[:limit]]
# Home page
@home_bp.route('/')
def index():
    events = db.session.scalars(
        db.select(Event).where(_active_event_clause())
    ).all()

    top_three = _select_upcoming_events(events)
    return render_template(
        'index.html',
        heading='Browse Events',
        events=events,
        upcoming_events=top_three
    )

@home_bp.route('/search')
def search():
    term = (request.args.get('search') or '').strip()

    # accept both [] and non-[] parameter names
    type_vals = request.args.getlist('event_type[]') + request.args.getlist('event_type')
    genre_vals = request.args.getlist('genre[]') + request.args.getlist('genre')
    status_vals = request.args.getlist('status[]') + request.args.getlist('status')

    upcoming_three = _select_upcoming_events(
        db.session.scalars(
            db.select(Event).where(_active_event_clause())
        ).all()
    )

    q = db.select(Event).where(_active_event_clause())

    # ---- text & price search (only if term provided) ----
    if term:
        query = f"%{term}%"
        filters = [
            Event.title.ilike(query),
            Event.description.ilike(query),
            Event.date.ilike(query),
            Event.venue.has(Venue.location.ilike(query)),
            Event.genres.any(Genre.genreType.ilike(query)),
            Event.artists.any(Artist.artistName.ilike(query)),
        ]

        price_value = _extract_price(term)
        if price_value is not None:
            min_price_ids = (
                db.select(Ticket.event_id)
                .group_by(Ticket.event_id)
                .having(func.min(Ticket.price) == price_value)
            )
            filters.append(Event.id.in_(min_price_ids))

        q = q.where(db.or_(*filters))

    # ---- event type filter (ids or names) ----
    if type_vals:
        from .models import EventType
        type_ids, type_names = [], []
        for v in type_vals:
            v = (v or '').strip()
            if not v:
                continue
            if v.isdigit():
                type_ids.append(int(v))
            else:
                type_names.append(v.lower())
        if type_ids:
            q = q.where(Event.event_type_id.in_(type_ids))
        if type_names:
            q = q.where(Event.event_type.has(func.lower(EventType.typeName).in_(type_names)))

    # ---- genre filter (ids or names) ----
    if genre_vals:
        genre_ids, genre_names = [], []
        for v in genre_vals:
            v = (v or '').strip()
            if not v:
                continue
            if v.isdigit():
                genre_ids.append(int(v))
            else:
                genre_names.append(v.lower())
        if genre_ids:
            q = q.where(Event.genres.any(Genre.id.in_(genre_ids)))
        if genre_names:
            q = q.where(Event.genres.any(func.lower(Genre.genreType).in_(genre_names)))

    # ---- status filter (normalize to UPPER) ----
    if status_vals:
        wanted = [s.strip().upper() for s in status_vals if s.strip()]
        if wanted:
            q = q.where(func.upper(Event.status).in_(wanted))

    events = db.session.scalars(q).all()

    if not events:
        flash('No events matched your filters. Try different filters or a keyword.', 'search_info')

    return render_template(
        'index.html',
        heading='Browse Events',
        events=events,
        search_term=term,
        upcoming_events=upcoming_three
    )


@home_bp.route('/help/faq')
def faq():
    # Render the Frequently Asked Questions page.
    return render_template('help/faq.html', heading='FAQ')


@home_bp.route('/help/contact')
def contact():
    # Render the Contact Us page.
    return render_template('help/contactUs.html', heading='Contact Us')


@home_bp.route('/help/privacy')
def privacy():
    # Render the Privacy Policy page.
    return render_template('help/privacypolicy.html', heading='Privacy Policy')


def _extract_price(raw_term: str):
    # Return a float price if the search term describes a ticket price.
    if not raw_term:
        return None

    lowered = raw_term.strip().lower()
    if "free" in lowered:
        return 0.0

    match = re.search(r"\d+(?:\.\d{1,2})?", raw_term)
    if not match:
        return None

    try:
        return round(float(match.group()), 2)
    except ValueError:
        return None