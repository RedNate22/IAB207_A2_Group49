from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

# Home page
@main_bp.route('/')
def index():
    return render_template('index.html')

# Event details
@main_bp.route('/eventdetails.html')
def eventdetails():
    return render_template('eventdetails.html')

# Create event
@main_bp.route('/createevent.html')
def createevent():
    return render_template('createevent.html')

# My tickets
@main_bp.route('/mytickets.html')
def mytickets():
    return render_template('mytickets.html')