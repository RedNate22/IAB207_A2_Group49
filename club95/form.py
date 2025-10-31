from datetime import datetime, date
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, IntegerField, HiddenField, TextAreaField
from wtforms.fields import DateField, TimeField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import NumberRange, Optional, EqualTo, Regexp, Email

#Sets up forms for use thorughout the application using Flask-WTF and WTForms
#https://wtforms.readthedocs.io/en/3.2.x/forms/ - Good read on WTForms

# adds forms for login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# adds forms for registration. Note that 15 is the max length for a phone number
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address.')])
    firstName = StringField('First Name', validators=[DataRequired()])
    lastName = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField(
        'Password', validators=[
            DataRequired(),
            Length(
                min=8,
                # Regex to ensure password complexity 
                message='Password must be at least 8 characters long.'),
            Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                message='Password must include at least one uppercase letter, one lowercase letter, one digit, and one special character.'),
            EqualTo('confirm_password', message='Passwords must match')
            ])
    confirm_password = PasswordField('Repeat Password', validators=[DataRequired()])
    phonenumber = StringField(
        'Phone No.',
        [
            DataRequired(),
            Length(min=10, max=10, message='Phone number must be 10 digits.'),
            Regexp(r'^\d{10}$', message='Enter a valid phone number.'),
        ],
        filters=[lambda x: x.replace(' ', '') if x else x],
    )
    streetAddress = StringField('Street Address', validators=[DataRequired(), Length(max=200)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=300)])
    profilePicture = FileField('Upload Image', validators=[Optional(), FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Register')

class EventForm(FlaskForm):
    # This form is used when creating a new event in the system
    # Each field here matches an input in the Create Event page template

    title = StringField('Event Title', validators=[DataRequired()])  # Name of the event
    date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])  # Date when the event will be held
    description = TextAreaField('Event Description', validators=[DataRequired(), Length(min=20, max=500)])  # Short description of the event (20-250 chars)
    location = StringField('Event Location', validators=[DataRequired()])  # Where the event takes place
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])  # When the event begins
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])  # When the event ends

    # A list of genres is fetched from the database and displayed as checkboxes
    genres = SelectMultipleField('Genres', coerce=int, validators=[DataRequired()])

    # Allows users to add a new genre if the one they want is not listed
    new_genre = StringField('Add New Genre', validators=[Length(max=50)])

    # Dropdown menu for selecting what kind of event it is (choices populated at runtime)
    type = SelectField('Type', choices=[], coerce=int, validators=[DataRequired()])

    # Image upload field for the event poster
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])

    # Hidden field to store which user created the event (filled automatically by the backend)
    user_id = HiddenField('Creator')

    # Submit button to create the event
    submit = SubmitField('Create Event')

    # Validate the event date to ensure it is not in the past
    def validate_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Event date cannot be in the past.')

    # Validate the start time to ensure it is not in the past
    def validate_start_time(self, field):
        event_date = self.date.data
        if not event_date or not field.data:
            return
        event_start = datetime.combine(event_date, field.data)
        now = datetime.now()
        # if date is today, check time is later today
        if event_date == date.today() and event_start <= now:
            raise ValidationError('Start time must be later than the current time for events scheduled today.')

    def validate_end_time(self, field):
        # Ensure the event finishes after it begins
        if not field.data or not self.start_time.data:
            return
        if field.data <= self.start_time.data:
            raise ValidationError('End time must be after the start time.')

class AddGenreForm(FlaskForm):
    # A simple form that lets users add a new genre to the database
    new_genre = StringField('Add New Genre', validators=[Length(max=50), DataRequired()])
    selected_genres = HiddenField('Selected Genres')
    submit = SubmitField('Add Genre')

class UpdateProfileForm(FlaskForm):
    # Form for updating user account details on the profile page
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address.')])
    firstName = StringField('First Name', validators=[DataRequired()])
    lastName = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Optional(),
                                Length(min=8,
                                    message='Password must be at least 8 characters long.'),
                                Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                    message='Password must include at least one uppercase letter, one lowercase letter, one digit, and one special character.'),
                                EqualTo('confirm_password', message='Passwords must match')
                                ])
    confirm_password = PasswordField('Repeat Password', validators=[Optional(), EqualTo('password', message='Passwords must match')])
    phonenumber = StringField(
        'Phone No.',
        [
            DataRequired(),
            Length(min=10, max=10, message='Phone number must be 10 digits.'),
            Regexp(r'^\d{10}$', message='Enter a valid phone number.'),
        ],
        filters=[lambda x: x.replace(' ', '') if x else x],
    )
    streetAddress = StringField('Street Address', validators=[DataRequired(), Length(max=200)])
    bio = TextAreaField('Bio', validators=[Length(max=300)])
    profilePicture = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')

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

            # Build a descriptive label including price and any perks
            perks_suffix = f" – {ticket.perks}" if getattr(ticket, "perks", None) else ""
            label = f"{ticket.ticketTier.capitalize()} (${'{:.2f}'.format(ticket.price)}){perks_suffix}"

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
                    "data-price": ticket.price,
                    "data-perks": ticket.perks or ""
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
    description = TextAreaField('Event Description', validators=[DataRequired(), Length(min=20, max=500)])  # Short description of the event
    location = StringField('Event Location', validators=[DataRequired()])  # Where the event takes place
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])  # When the event begins
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])  # When the event ends

    # A list of genres is fetched from the database and displayed as checkboxes
    genres = SelectMultipleField('Genres', coerce=int, validators=[DataRequired()])

    # Allows users to add a new genre if the one they want is not listed
    new_genre = StringField('Add New Genre', validators=[Length(max=50)])

    # Dropdown menu for selecting what kind of event it is (choices populated at runtime)
    type = SelectField('Type', choices=[], coerce=int, validators=[DataRequired()])

    # Image upload field for the event poster
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])

    # Hidden field to store which user created the event (filled automatically by the backend)
    user_id = HiddenField('Creator')

    # Submit button to create the event
    submit = SubmitField('Update Event')

    def validate_end_time(self, field):
        # Ensure the event finishes after it begins
        if not field.data or not self.start_time.data:
            return
        if field.data <= self.start_time.data:
            raise ValidationError('End time must be after the start time.')