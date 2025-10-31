import os

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func, cast

from club95.form import UpdateProfileForm
from .models import Order, OrderTicket, Ticket, Event, Venue, Genre, EventType
from . import db
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

user_bp = Blueprint('user_bp', __name__, template_folder='templates')


def format_phone_display(number: str) -> str:
    if not number:
        return None
    digits = ''.join(ch for ch in number if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    return number

# My tickets page
@user_bp.route('/user/mytickets')
@login_required
def mytickets():
    term = (request.args.get('search') or '').strip()

    # Accept BOTH bracketed and non-bracketed names
    event_types_raw = request.args.getlist('event_type[]') or request.args.getlist('event_type')
    genres_raw      = request.args.getlist('genre[]')      or request.args.getlist('genre')
    statuses_raw    = request.args.getlist('status[]')     or request.args.getlist('status')

    statuses = [s.upper() for s in statuses_raw]

    et_ids   = [int(v) for v in event_types_raw if v.isdigit()]
    et_names = [v for v in event_types_raw if not v.isdigit()]

    g_ids    = [int(v) for v in genres_raw if v.isdigit()]
    g_names  = [v for v in genres_raw if not v.isdigit()]

    q = (
        db.select(Order)
        .join(OrderTicket, OrderTicket.order_id == Order.id)
        .join(Ticket, Ticket.id == OrderTicket.ticket_id)
        .join(Event, Event.id == Ticket.event_id)
        .outerjoin(Venue, Venue.id == Event.venue_id)
        .options(
            joinedload(Order.line_items)
            .joinedload(OrderTicket.ticket)
            .joinedload(Ticket.event)
            .joinedload(Event.venue)
        )
        .where(Order.user_id == current_user.id)
    )

    if term:
        like = f"%{term}%"
        q = q.where(
            db.or_(
                Event.title.ilike(like),
                Event.description.ilike(like),
                cast(Event.date, db.String).ilike(like),
                Venue.location.ilike(like),
                Event.genres.any(Genre.genreType.ilike(like)),
            )
        )

    if et_ids:
        q = q.where(Event.event_type.has(EventType.id.in_(et_ids)))
    if et_names:
        q = q.where(Event.event_type.has(EventType.typeName.in_(et_names)))

    if g_ids:
        q = q.where(Event.genres.any(Genre.id.in_(g_ids)))
    if g_names:
        q = q.where(Event.genres.any(Genre.genreType.in_(g_names)))

    if statuses:
        q = q.where(func.upper(Event.status).in_(statuses))

    # Execute query
    orders = db.session.scalars(q.distinct()).unique().all()

    # --- Keep only the line items whose event matches the active filters ---
    # Helper: checks if an event satisfies current filters/search.
    def _event_matches(ev) -> bool:
        if not ev:
            return False

        # Text search (case-insensitive, covers title/description/venue/genres/date as string)
        if term:
            t = term.lower()
            if not (
                (getattr(ev, "title", None) and t in ev.title.lower()) or
                (getattr(ev, "description", None) and t in ev.description.lower()) or
                (getattr(getattr(ev, "venue", None), "location", None) and t in ev.venue.location.lower()) or
                any(getattr(g, "genreType", None) and t in g.genreType.lower() for g in getattr(ev, "genres", []) or []) or
                (str(getattr(ev, "date", "")) and t in str(getattr(ev, "date", "")).lower())
            ):
                return False

        # Event type filter (IDs or names)
        if et_ids or et_names:
            et = getattr(ev, "event_type", None)
            et_ok = False
            if et:
                if et_ids and getattr(et, "id", None) in et_ids:
                    et_ok = True
                if et_names and getattr(et, "typeName", None) in et_names:
                    et_ok = True
            if not et_ok:
                return False

        # Genre filter (IDs and/or names)
        if g_ids or g_names:
            ev_genres = getattr(ev, "genres", []) or []
            g_ids_ok = (not g_ids) or any(getattr(g, "id", None) in g_ids for g in ev_genres)
            g_names_ok = (not g_names) or any(getattr(g, "genreType", None) in g_names for g in ev_genres)
            if not (g_ids_ok and g_names_ok):
                return False

        # Status filter (already upper-cased in request parsing)
        if statuses:
            ev_status = (getattr(ev, "status", "") or "").upper()
            if ev_status not in statuses:
                return False

        return True

    # Build a filtered view-model per order
    orders_vm = []
    for od in orders:
        visible_items = []
        for li in od.line_items:
            tk = getattr(li, "ticket", None)
            ev = getattr(tk, "event", None) if tk else None
            if _event_matches(ev):
                visible_items.append(li)
        if visible_items:
            # Attach a transient attribute for the template to iterate
            od.visible_items = visible_items
            orders_vm.append(od)

    if not orders_vm:
        flash("No tickets matched your filters. Try a different keyword or filter.", "search_info")

    return render_template(
        "user/mytickets.html",
        heading="My Tickets",
        orders=orders_vm,   # pass filtered orders with per-order visible_items
        search_term=term,
    )


# User profile page

@user_bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)
    editing = False
    def populate_form_from_user():
        form.firstName.data = current_user.firstName
        form.lastName.data = current_user.lastName
        form.email.data = current_user.email
        form.phonenumber.data = format_phone_display(current_user.phoneNumber)
        form.streetAddress.data = current_user.streetAddress
        form.bio.data = current_user.bio
        form.profilePicture.data = None
        form.password.data = ''

    if request.method == 'GET':
        populate_form_from_user()
    if request.method == 'POST' and 'edit' in request.form:
        editing = True
        populate_form_from_user()
    elif form.validate_on_submit():
        # Only update fields if provided
        if form.email.data:
            current_user.email = form.email.data
        if form.firstName.data:
            current_user.firstName = form.firstName.data
        if form.lastName.data:
            current_user.lastName = form.lastName.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data, method='scrypt', salt_length=16)
        if form.phonenumber.data:
            current_user.phoneNumber = form.phonenumber.data
        if form.streetAddress.data:
            current_user.streetAddress = form.streetAddress.data
        if form.bio.data:
            current_user.bio = form.bio.data
        if form.profilePicture.data and getattr(form.profilePicture.data, 'filename', ''):
            filename = secure_filename(form.profilePicture.data.filename)
            if filename:
                upload_dir = os.path.join('club95', 'static', 'img')
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, filename)
                form.profilePicture.data.save(save_path)
                current_user.profilePicture = os.path.join('img', filename).replace('\\', '/')
        db.session.commit()
        db.session.refresh(current_user)
        editing = False
        populate_form_from_user()
    elif request.method == 'POST':
        editing = True
    formatted_phone = format_phone_display(current_user.phoneNumber)
    return render_template('user/user.html', form=form, editing=editing, user=current_user, formatted_phone=formatted_phone)
