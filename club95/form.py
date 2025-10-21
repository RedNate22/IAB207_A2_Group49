from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, IntegerField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import NumberRange,Optional

#Sets up forms for use thorughout the application using Flask-WTF and WTForms
#https://wtforms.readthedocs.io/en/3.2.x/forms/ - Good read on WTForms

# adds forms for login
class LoginForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# adds forms for registration. Note that 15 is the max length for a phone number
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    phonenumber = StringField('Phone No.', [Length(min=4, max=25)])
    submit = SubmitField('Register')

# TODO: Ana - now that I have updated the database I need you to update these forms for me
# note keep FileField for image upload
# adds forms for creating events

class EventForm(FlaskForm):
    # This form is used when creating a new event in the system
    # Each field here matches an input in the Create Event page template

    title = StringField('Event Title', validators=[DataRequired()])  # Name of the event
    date = StringField('Event Date', validators=[DataRequired()])  # Date when the event will be held
    description = StringField('Event Description', validators=[DataRequired()])  # Short description of the event
    location = StringField('Event Location', validators=[DataRequired()])  # Where the event takes place
    start_time = StringField('Start Time', validators=[DataRequired()])  # When the event begins
    end_time = StringField('End Time', validators=[DataRequired()])  # When the event ends

    # A list of genres is fetched from the database and displayed as checkboxes
    genres = SelectMultipleField('Genres', coerce=int, validators=[DataRequired()])

    # Allows users to add a new genre if the one they want is not listed
    new_genre = StringField('Add New Genre', validators=[Length(max=50)])

    # Dropdown menu for selecting what kind of event it is
    type = SelectField('Type', choices=[
        ('Live Concert', 'Live Concert'),
        ('Music Festival', 'Music Festival'),
        ('Orchestra', 'Orchestra'),
        ('DJ Set', 'DJ Set'),
        ('Solo Artist Performance', 'Solo Artist Performance')
    ], validators=[DataRequired()])



    # Image upload field for the event poster
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])

    # Hidden field to store which user created the event (filled automatically by the backend)
    user_id = HiddenField('Creator')

    # Submit button to create the event
    submit = SubmitField('Create Event')


class AddGenreForm(FlaskForm):
    # A simple form that lets users add a new genre to the database
    new_genre = StringField('Add New Genre', validators=[Length(max=50), DataRequired()])
    submit = SubmitField('Add Genre')


class UpdateProfileForm(FlaskForm):
    # Form for updating user account details on the profile page
    email = StringField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    Password = PasswordField('Password', validators=[DataRequired()])
    phonenumber = StringField('Phone No.', [Length(min=4, max=25)])
    submit = SubmitField('Update Profile')

# TODO: Nate - Ticket buying forms and creating new ticket tiers for events
class TicketPurchaseForm(FlaskForm):
    submit = SubmitField('Purchase')

    def __init__(self, ticket_tiers, formdata = None, *args, **kwargs):
        # call constructor of parent class (FlaskForm)
        super().__init__(formdata = formdata, *args, **kwargs)

        # Bind quantity field for each ticket tier on the instance
        # i.e each ticket tier gets its own quantity
        for ticket in ticket_tiers:
            # create unique field name based on ticket ID
            field_name = f"quantity_{ticket.id}"

            # Set format for ticket prices and add $
            # format price to floating point with 2 decimal places
            label = f"{ticket.ticketTier.capitalize()} (${'{:.2f}'.format(ticket.price)})"

            # (fields are built dynamically)
            unbound_field = IntegerField(
                label, 
                validators = [Optional(), NumberRange(min = 0)],
                default = 0,  # avoid unassigned

                # Set HTML attributes for each ticket tier row
                render_kw = {
                    "class": "form-control",
                    "min": 0,
                    "max": ticket.availability,
                    "id": f"quantity-{ticket.id}",
                    "data-tier": ticket.ticketTier,
                    "data-price": ticket.price    
                    }
                )

            ## Bind field to form
            # Attach field to this form instance with dynamic name
            bound_field = unbound_field.bind(form = self, name = field_name)
            # Initialise field value using submitted data or default
            bound_field.process(formdata, bound_field.default)
            # Register field in Flask-WTF interal dictionary
            # to be indexed and accessible by name when requested
            self._fields[field_name] = bound_field
            # Grab form and assign it a name (provided by database), grab integer that was bound
            setattr(self, field_name, bound_field)

# form for creating a comment on an event
class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=300)])
    submit = SubmitField('Post')



class updateEvent(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])  # Name of the event
    date = StringField('Event Date', validators=[DataRequired()])  # Date when the event will be held
    description = StringField('Event Description', validators=[DataRequired()])  # Short description of the event
    location = StringField('Event Location', validators=[DataRequired()])  # Where the event takes place
    start_time = StringField('Start Time', validators=[DataRequired()])  # When the event begins
    end_time = StringField('End Time', validators=[DataRequired()])  # When the event ends

    # A list of genres is fetched from the database and displayed as checkboxes
    genres = SelectMultipleField('Genres', coerce=int, validators=[DataRequired()])

    # Allows users to add a new genre if the one they want is not listed
    new_genre = StringField('Add New Genre', validators=[Length(max=50)])

    # Dropdown menu for selecting what kind of event it is
    type = SelectField('Type', choices=[
        ('Live Concert', 'Live Concert'),
        ('Music Festival', 'Music Festival'),
        ('Orchestra', 'Orchestra'),
        ('DJ Set', 'DJ Set'),
        ('Solo Artist Performance', 'Solo Artist Performance')
    ], validators=[DataRequired()])

    # Image upload field for the event poster
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])

    # Hidden field to store which user created the event (filled automatically by the backend)
    user_id = HiddenField('Creator')

    # Submit button to create the event
    submit = SubmitField('Update Event')
 