from flask import Blueprint, render_template, request, redirect, url_for
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
    if request.args.get('search') and request.args.get('search') != "":
        print(request.args['search'])
        query = "%" + request.args['search'] + "%"
        events = db.session.scalars(db.select(Event).where(Event.title.like(query))).all()
        return render_template('index.html', heading='Browse Events', events=events)
    else:
        return redirect(url_for('home_bp.index'))