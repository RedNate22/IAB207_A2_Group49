from flask import Blueprint, render_template

home_bp = Blueprint('home_bp', __name__)

# Home page
@home_bp.route('/')
def index():
    return render_template('index.html')