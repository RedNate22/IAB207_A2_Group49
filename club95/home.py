import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from .models import Artist, Event, Genre, Ticket
from . import db

home_bp = Blueprint('home_bp', __name__, template_folder='templates')

# Home page
@home_bp.route('/')
def index():
    event = db.session.scalars(db.select(Event)).all()
    return render_template('index.html', heading='Browse Events', events=event)

@home_bp.route('/search')
def search():
    term = (request.args.get('search') or '').strip()
    if not term:
        return redirect(url_for('home_bp.index'))

    query = f"%{term}%"
    price_value = _extract_price(term)

    filters = [
        Event.title.ilike(query),
        Event.genres.any(Genre.genreType.ilike(query)),
        Event.location.ilike(query),
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
        .where(db.or_(*filters))
    ).all()
    

    if not events:
        flash(f'No events found for "{term}". Try another title or keyword.', 'search_info')

    return render_template(
        'index.html',
        heading='Browse Events',
        events=events,
        search_term=term
    )


def _extract_price(raw_term: str):
    """Return a float price if the search term describes a ticket price."""
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