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
    title = StringField('Event Title', validators=[DataRequired()])
    date = StringField('Event Date', validators=[DataRequired()])
    description = StringField('Event Description', validators=[DataRequired()])
    location = StringField('Event Location', validators=[DataRequired()])
    start_time = StringField('Start Time', validators=[DataRequired()])
    end_time = StringField('End Time', validators=[DataRequired()])
    genres = SelectMultipleField('Genres', coerce=int, validators=[DataRequired()])  # choices set in route
    new_genre = StringField('Add New Genre', validators=[Length(max=50)])
    artists = SelectMultipleField('Artists', coerce=int)  # choices set in route
    new_artist = StringField('Add New Artist', validators=[Length(max=150)])
    type = SelectField('Type', choices=[
        ('Live Concert','Live Concert'),
        ('Music Festival','Music Festival'),
        ('Orchestra','Orchestra'),
        ('DJ Set','DJ Set'),
        ('Solo Artist Performance','Solo Artist Performance')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('OPEN','OPEN'), ('INACTIVE','INACTIVE'),
        ('SOLD OUT','SOLD OUT'), ('CANCELLED','CANCELLED')
    ], validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Create Event')


class AddGenreForm(FlaskForm):
    new_genre = StringField('Add New Genre', validators=[Length(max=50), DataRequired()])
    submit = SubmitField('Add Genre')

# adds forms for updating user profile
class UpdateProfileForm(FlaskForm):
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
        for ticket in ticket_tiers:
            field_name = f"quantity_{ticket.id}"

            # Set format for ticket prices and add $
            label = f"{ticket.ticketTier.capitalize()} (${'{:.2f}'.format(ticket.price)})"
            unbound_field = IntegerField(
                label, 
                validators = [Optional(), NumberRange(min = 0)],
                default = 0,
                render_kw = {
                    "class": "form-control",
                    "min": 0,
                    "max": ticket.availability,
                    "id": f"quantity-{ticket.id}",
                    "data-tier": ticket.ticketTier,
                    "data-price": ticket.price    
                    }
                )
            bound_field = unbound_field.bind(form = self, name = field_name)
            bound_field.process(formdata, bound_field.default)
            self._fields[field_name] = bound_field
            setattr(self, field_name, bound_field)

# form for creating a comment on an event
class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=300)])
    submit = SubmitField('Post')
