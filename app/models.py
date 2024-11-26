from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

class Client(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    is_organization = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False)

    full_name = db.Column(db.String(60))
    date_of_birth = db.Column(db.String(60))
    email = db.Column(db.String(120), unique=True)
    phonenumber = db.Column(db.String(16), unique=True)
    affiliated_area = db.Column(db.String(120))
    password = db.Column(db.String(60))
    profile_pic = db.Column(db.String(120), default="default_user.jpg")

    answered_organization_questions = db.Column(db.Boolean, default=False)
    events_registered_for = db.Column(db.String, default=None)

    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    events_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    
    def __repr__(self):
        output = ""
        if self.is_organization == True:
            output = ": Organization"
        else:
            output = ": Customer"

        return f"{self.full_name} ({self.email}){output}"

class Organization(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    organization_name = db.Column(db.String(120), default=None)
    primary_location = db.Column(db.String(120), default=None)
    mission_statement = db.Column(db.String(240), default=None)
    email_contact = db.Column(db.String(120), default=None)
    phonenumber_contact = db.Column(db.String(120), default=None)
    website_link = db.Column(db.String(120), default=None)
    image = db.Column(db.String(120), default="default_organization.jpg")
    security_code = db.Column(db.String(120), default=None)

    administrators = db.relationship("Client", backref="administrator")
    events = db.relationship("Event", backref="event")

    def __repr__(self):
        return f"\n\n<{self.organization_name}:\nAdministrators:{self.administrators}>\n\n"

class Event(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    event_name = db.Column(db.String(120))
    event_startdate = db.Column(db.String(120))
    event_enddate = db.Column(db.String(120))
    event_starttime = db.Column(db.String(120))
    event_endtime = db.Column(db.String(120))
    event_location = db.Column(db.String(120))
    event_max_volunteers = db.Column(db.String(120))
    event_min_age = db.Column(db.String(120))
    event_max_age = db.Column(db.String(120))
    event_category = db.Column(db.String(120))
    event_description = db.Column(db.String(120))
    event_age_range = db.Column(db.String(120))
    event_keywords = db.Column(db.String(620))
    event_img = db.Column(db.String(620))

    post_date = db.Column(db.String(120))
    post_time = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    for_display_event_datetime = db.Column(db.String(120))
    for_display_post_datetime = db.Column(db.String(120))
    days_until_event = db.Column(db.String(120))
    last_updated = db.Column(db.String(120))
    
    keywords = db.relationship("Keyword", backref="keywords")
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    registrees = db.relationship("Client", backref="registree")

    def __repr__(self):
        return f"\n\n{self.event_name}: Organization ID: {self.organization_id}\n\n"

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.String(120))
    color = db.Column(db.String(60))

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

    def __repr__(self):
        return f"{self.phrase} --> {Event.query.filter_by(id=self.event_id).first().event_name}"
