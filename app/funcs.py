from app import app, db, mail, Serializer
from app.models import Organization, Client, Event, Keyword
from flask_login import current_user
from flask import flash, redirect, url_for
from datetime import date, datetime
from random import randint
import secrets
from PIL import Image
from email_validator import validate_email, EmailNotValidError
import bcrypt
import os
from flask_mail import Message
import random
from flask_login import login_user

def db_reset(sign_in_as):
    db.drop_all()
    db.create_all()

    create_admin = Client(is_organization=True, is_confirmed=True, full_name="Admin", date_of_birth="01/23/2003", email="admin@gmail.com", phonenumber="2242270113", affiliated_area="Chicago, Illinois", password=encrypt_password("password1"), profile_pic=str(url_for('static', filename='default_imgs/'+"default_user.jpg")), answered_organization_questions=True, organization_id=1)
    create_user = Client(is_organization=False, is_confirmed=True, full_name="User", date_of_birth="05/11/2007", email="user@gmail.com", phonenumber="6368991252", affiliated_area="Chicago, Illinois", password=encrypt_password("password2"), profile_pic=str(url_for('static', filename='default_imgs/'+"default_user.jpg")))
    
    db.session.add(create_admin)
    db.session.add(create_user)

    db.session.commit()

    if sign_in_as == "User":
        login_user(Client.query.filter_by(email="user@gmail.com").first())
    elif sign_in_as == "Admin":
        login_user(Client.query.filter_by(email="admin@gmail.com").first())

    create_organization = Organization(organization_name="Organization", primary_location="Chicago, IL", mission_statement="Empowering the upcoming generation, one event at a time.", email_contact="organization@gmail.com", phonenumber_contact="8471120324", website_link="https://www.google.com/", image=str(url_for('static', filename='default_imgs/'+"default_organization.jpg")), security_code="123456")
    db.session.add(create_organization)
    org_obj = Organization.query.filter_by(id=1).first()
    list(org_obj.administrators).append(Client.query.filter_by(email="admin@gmail.com"))

    db.session.commit()

def db_create_event():
    current_post_time = datetime.now().strftime("%I:%M:%S %p")
    current_post_date = date.today().strftime("%b %d, %Y")

    new_event = Event(event_name="Dummy Event", event_startdate="12/10/2025", event_enddate="12/10/2025", event_starttime="8:00 AM", event_endtime="2:00 PM", event_location="1500 Longwood Drive, Algonquin IL, 502123", event_max_volunteers="10", event_min_age="15", event_max_age="18", event_category="Religious", event_description="Come help out!", event_keywords="Friendly, energetic", event_img=str(url_for('static', filename='default_imgs/'+"default_event.jpeg")), post_date=current_post_date, post_time=current_post_time, organization_id=current_user.organization_id)
    db.session.add(new_event)
    db.session.commit()
    rand_colors = get_random_colors(len(string_to_list(new_event.keywords)))
    for i in rand_colors:
        new_kw = Keyword(phrase=str(string_to_list(new_event.keywords)[rand_colors.index(i)]), color=str(i), event_id=new_event.id)
        db.session.add(new_kw)
        list(new_event.keywords).append(new_kw)
    db.session.commit()

def validate_category(user_category):
    if user_category == "Pick a category...":
        return False
    
    return True

def validate_date(user_date):
    format = "%m/%d/%Y"
    res = True
    try:
        res = bool(datetime.strptime(user_date, format))
    except ValueError:
        res = False

    return res

def get_badge_colors():
    badge_colors = ["primary", "secondary", "success", "warning", "info", "danger"]
    return badge_colors

def get_random_colors(num_of_kws):
    output = []
    all_colors = get_badge_colors()
    output = random.sample(all_colors, int(num_of_kws))
    return output

def check_organization_status():
    if current_user.is_organization == True:
        if current_user.answered_organization_questions == True:
            return True
        else:
            flash("You must create your organization first by answering questions about it.", "warning")
            return redirect(url_for("orginfo", user_id=current_user.id))
    else:
        flash("You are not an administrator for an organization. Please contact your organization if you think this is a mistake.", "warning")
        return redirect(url_for("home"))

def check_authenticated_email():
    authenticated = False
    if current_user.is_confirmed == False:
        token = str(Serializer.dumps(current_user.email, salt="email-confirmation"))
        send_authentication_email(current_user.email, token)
        flash("Your account has not been activated yet. An email has just been sent to you to activate your account.", "primary")
        authenticated = False
        return redirect(url_for("home"))
    else:
        authenticated = True

    return authenticated

def check_age(dob, event_obj):
    today = date.today()
    dob = datetime(int(dob[0:4]), int(dob[5:7]), int(dob[8:]))
    user_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if int(event_obj.event_min_age) <= int(user_age) <= int(event_obj.event_max_age):
        return True
    else:
        return False

def check_max_participants_reached(event_obj):
    if int(len(event_obj.registrees)) + 1 <= int(event_obj.event_max_volunteers):
        return True
    else:
        return False

def get_user_upcoming_events():
    output = []
    all_events = Event.query.filter_by(is_active=True).all()
    for e in all_events:
        if current_user in e.registrees:
            output.append(e)

    return output

def get_user_completed_events():
    output = []
    all_events = Event.query.filter_by(is_active=False).all()
    for e in all_events:
        if current_user in e.registrees:
            output.append(e)

    return output

def check_too_many_events():
    user_events = get_user_upcoming_events()
    if user_events == []:
        user_events = 0
    else:
        user_events = len(user_events)

    if user_events >= 3:
        return False
    else:
        return True

def check_signup_status(event_obj):
    if current_user in event_obj.registrees:
        return False
    else:
        return True

def get_random_code(n=6):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def save_picture(form_picture, for_event_or_org=False):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + str(f_ext)
    picture_path = os.path.join(app.root_path, 'static\images', picture_fn)
    if for_event_or_org==False:
        output_size = (150,150)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    else:
        i = Image.open(form_picture)
        i.save(picture_path)

    return picture_fn

def check_email(email, check_deliv):
    boolean_email_msg_return = []

    if email_unique(email) == True:

        try:
            emailinfo = validate_email(email, check_deliverability=check_deliv)

            email = emailinfo.normalized

            boolean_email_msg_return.append(True)
            boolean_email_msg_return.append(email)
            boolean_email_msg_return.append(None)

            return boolean_email_msg_return

        except EmailNotValidError as exception_description:
            boolean_email_msg_return.append(False)
            boolean_email_msg_return.append(email)
            boolean_email_msg_return.append(exception_description)

            return boolean_email_msg_return
        
    else:
        boolean_email_msg_return.append(False)
        boolean_email_msg_return.append(email)
        boolean_email_msg_return.append("That email already exists in our database. Please try again.")

        return boolean_email_msg_return

def email_unique(email):
    all_emails = get_all_emails()
    
    if email in all_emails:
        return False
    
    return True

def unique_phonenumber(pn):
    all_phonenumbers = get_all_phonenumbers()
    
    if pn in all_phonenumbers:
        return False
    
    return True

def check_password(password_field, confirm_password_field):
    if password_field == confirm_password_field:
        return True
    else:
        return False

def get_is_organization_value(is_organization_field):
    if is_organization_field == "organization":
        return True
    
    return False

def get_all_organization_objs():
    all_org_objs = []

    for org in Organization.query.all():
        all_org_objs.append(org)

    return all_org_objs

def send_authentication_email(user_email, token):
    msg = Message('Account Activation', sender=app.config['MAIL_USERNAME'], recipients=[user_email])
    msg.body = f'''

    Thank you for signing up! To activate your account, please follow the link below:

    {url_for("confirm_email", token=token, _external=True)}
    
    '''
    
    mail.send(msg)

def encrypt_password(password):
    new_password = ""

    password = password.encode("utf-8")
    new_password = bcrypt.hashpw(password, bcrypt.gensalt())

    return new_password

def get_all_emails():
    all_emails_list = []
    for user_obj in Client.query.all():
        all_emails_list.append(user_obj.email)
    return all_emails_list

def get_all_phonenumbers():
    all_phonenumbers_list = []
    for user_obj in Client.query.all():
        all_phonenumbers_list.append(user_obj.phonenumber)
    return all_phonenumbers_list

def check_for_not_active_events():
    all_events = Event.query.all()
    for event in all_events:
        is_active = True

        current_time = convertto24(datetime.now().strftime("%I:%M:%S %p"))
        event_time = event.event_starttime

        current_date = str(date.today())
        event_date = str(date(int(event.event_startdate[0:4]), int(str(event.event_startdate)[5:7]), int(event.event_startdate[8:])))
        event_enddate = str(date(int(event.event_enddate[0:4]), int(str(event.event_enddate)[5:7]), int(event.event_enddate[8:])))

        current_datetime = str(datetime(int(current_date[0:4]), int(current_date[5:7]), int(current_date[8:]), int(current_time[0:2]), int(current_time[3:5])))
        event_datetime = str(datetime(int(event_date[0:4]), int(event_date[5:7]), int(event_date[8:]), int(event_time[0:2]), int(event_time[3:5])))

        event_enddate_datetime = str(datetime(int(event_enddate[0:4]), int(event_enddate[5:7]), int(event_enddate[8:]), int(event.event_endtime[0:2]), int(event.event_endtime[3:5])))

        if (current_datetime > event_datetime) and (current_datetime > event_enddate_datetime):
            is_active = False
        else:
            is_active = True
            
        if str(event.event_startdate) == str(event.event_enddate):
            display_datetime = datetime(int(event_date[0:4]), int(event_date[5:7]), int(event_date[8:])).strftime("%b %d")
        else:
            display_datetime = datetime(int(event_date[0:4]), int(event_date[5:7]), int(event_date[8:])).strftime("%b %d")
            display_datetime += " to " + str(datetime(int(event_enddate[0:4]), int(event_enddate[5:7]), int(event_enddate[8:])).strftime("%b %d"))

        display_datetime += ", " + str(datetime.strptime(f"{int(event_time[0:2])}:{int(event_time[3:5])}", "%H:%M").strftime("%I:%M %p"))
        display_datetime += " to " + str(datetime.strptime(f"{int(event.event_endtime[0:2])}:{int(event.event_endtime[3:5])}", "%H:%M").strftime("%I:%M %p"))

        event.for_display_event_datetime = display_datetime

        display_posttime = event.post_date + " at " + event.post_time
        event.for_display_post_datetime = display_posttime
        
        event.is_active = is_active

        delta = difference_between_dates(current_datetime, event_datetime, is_active)
        event.days_until_event = delta

        if event.last_updated == None or event.last_updated == "":
            event.last_updated = display_posttime

        db.session.commit()

def string_to_list(string_of_words):
    list_of_words = []
    output = []

    list_of_words = str(string_of_words).split(",")
    for i in list_of_words:
        output.append(str(i.strip()).capitalize())

    return output

def convertto24(time_input): 
    if time_input[-2:] == "AM" and time_input[:2] == "12": 
        return "00" + time_input[2:-2] 
      
    elif time_input[-2:] == "AM": 
        return time_input[:-2] 
     
    elif time_input[-2:] == "PM" and time_input[:2] == "12": 
        return time_input[:-2] 
    
    else: 
        return str(int(time_input[:2]) + 12) + time_input[2:8]

def difference_between_dates(current_dt, event_dt, is_active):
    delta = ""

    cdt = datetime.strptime(current_dt, "%Y-%m-%d %H:%M:%S")
    edt = datetime.strptime(event_dt, "%Y-%m-%d %H:%M:%S")
    
    if is_active:
        delta = str((edt - cdt).days)
    else:
        delta = str((cdt - edt).days)

    return delta

