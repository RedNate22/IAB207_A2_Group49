from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Event
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
    events = db.session.scalars(
        db.select(Event).where(Event.title.ilike(query))
    ).all()

    if not events:
        flash(f'No events found for "{term}". Try another title or keyword.', 'search_info')

    return render_template(
        'index.html',
        heading='Browse Events',
        events=events,
        search_term=term
    )