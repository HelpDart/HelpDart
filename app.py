from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, TextAreaField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import InputRequired, ValidationError
from email_validator import validate_email, EmailNotValidError
from datetime import date, datetime
import bcrypt
from fuzzywuzzy import fuzz, process
import secrets
import os
from PIL import Image
from random import choice, randint
import math
from scripts import check_organization_status

db = SQLAlchemy()

event_categories = ["Animals/Veterinary", "Religious", "Medical", "Military", "Arts/Literature", "Sports", "Youth/Education", "Nature/Outdoors", "Community", "Philanthropy/General", "Other"]
badge_colors = ["bg-primary", "bg-secondary", "bg-success", "bg-warning", "bg-info", "bg-danger"]

def create_app():
    app = Flask(__name__)
    
    app.config["SECRET_KEY"] = "helpdart"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    
    db.init_app(app)

    return app

app = create_app()
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

@app.route("/", methods=["GET", "POST"])    
@app.route("/home", methods=["GET", "POST"])
def home():
    check_for_not_active_events()
    all_events = Event.query.filter_by(is_active=True).all()
    sign_up_form = EventSignUpForm()

    if request.method == "POST":
        if sign_up_form.validate_on_submit():
            print(request.form.get("signupforeventbtn"))

    return render_template("home.html", all_events=all_events, sign_up_form=sign_up_form, Organization=Organization)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if request.method == "POST":
        if form.validate_on_submit():
            user_email = form.email.data
            user_password = form.password.data
            signed_up_user_emails = get_all_emails()
            
            if user_email in signed_up_user_emails:
                if bcrypt.checkpw(user_password.encode("utf-8"), Client.query.filter_by(email=user_email).first().password):
                    login_user(Client.query.filter_by(email=user_email).first())

                    if current_user.is_organization == True and current_user.answered_organization_questions == False:
                        flash("Please fill out the following information about your organization.", "info")
                        return redirect(url_for("orginfo", user_id=current_user.id))
                    else:
                        flash("You have been successfully logged in.", "success")
                        return redirect(url_for("home"))
                else:
                    flash("Incorrect password, please try again.", "warning")
                    return redirect(url_for("login"))
            else:
                flash("You have not registered yet.", "warning")
                return redirect(url_for("register"))

    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if request.method == "POST":
        if form.validate_on_submit():
            user_fullname = form.fullname.data
            user_email = form.email.data
            user_password = form.password.data
            user_confirm_password = form.confirm_password.data
            user_is_organization = get_is_organization_value(request.form.get("is_organization"))

            email_check_list = check_email(user_email, True)
            user_email = email_check_list[1]
            password_check = check_password(user_password, user_confirm_password)

            if email_check_list[0] == False:
                flash("There was an issue with your email. Please try again.", "warning")
                return redirect(url_for("register"))
            elif password_check == False:
                flash("Your passwords do not match. Please try again.", "warning")
                return redirect(url_for("register"))
            
            new_user = Client(is_organization=user_is_organization, full_name=user_fullname, email=user_email, password=encrypt_password(user_password))
            db.session.add(new_user)
            db.session.commit()
            login_user(Client.query.filter_by(email=user_email).first())
            if user_is_organization == True:
                flash("Your account has been created. Please fill out the following information about your organization.", "info")
                return redirect(url_for("orginfo", user_id=new_user.id))
            else:
                flash("You have been successfully registered!", "success")
                return redirect(url_for("home"))

    return render_template("register.html", form=form)

@app.route("/orginfo/<user_id>/", methods=["GET", "POST"])
@login_required
def orginfo(user_id):
    form = OrganizationInforForm()
    user_obj = Client.query.filter_by(id=user_id).first()
    page_intro_msg = ""

    if user_obj.is_authenticated == True:

        if user_obj.answered_organization_questions == False:
            page_intro_msg = "To create your organization, please answer the following questions regarding it."

            if request.method == "POST":
                if form.validate_on_submit():
                    if form.org_image.data:
                        picture_file = save_picture(form.org_image.data)
                        picture_file = f"{app.root_path[51:]}\static\images\{picture_file}"
                    else:
                        flash("Please provide a valid image that represents your organization (image of organization headquarters, organization logo, etc.).", "warning")
                        return redirect(url_for("orginfo", user_id=current_user.id))

                    new_org_info_obj = Organization(organization_name=form.organization_name.data, primary_location= form.primary_location.data, mission_statement= form.mission_statement.data, email_contact= form.email_contact.data, phonenumber_contact= form.phonenumber_contact.data, website_link= form.website_link.data, image=picture_file, security_code=str(get_random_code()))
                    db.session.add(new_org_info_obj)
                    db.session.commit()
                    current_user.answered_organization_questions = True
                    current_user.organization_id = new_org_info_obj.id
                    db.session.commit()
                    
                    flash("Your organization information has been saved.", "success")
                    return redirect(url_for("account"))

            return render_template("orginfo.html", form=form, user_obj=user_obj, page_intro_msg=page_intro_msg)
        
        else:
            organization_obj = Organization.query.filter_by(id=current_user.organization_id).first()

            if request.method == "GET":

                form.organization_name.data = organization_obj.organization_name
                form.primary_location.data = organization_obj.primary_location
                form.mission_statement.data = organization_obj.mission_statement
                form.email_contact.data = organization_obj.email_contact
                form.phonenumber_contact.data = organization_obj.phonenumber_contact
                form.website_link.data = organization_obj.website_link
                form.org_image.data = organization_obj.image

                page_intro_msg = "You have already provided information regarding your organization. You may edit that information now."

            elif request.method == "POST":
                organization_obj.organization_name = form.organization_name.data
                organization_obj.primary_location = form.primary_location.data
                organization_obj.mission_statement = form.mission_statement.data
                organization_obj.email_contact = form.email_contact.data
                organization_obj.phonenumber_contact = form.phonenumber_contact.data
                organization_obj.website_link = form.website_link.data

                if form.org_image.data == None:
                    organization_obj.image = organization_obj.image
                else:
                    organization_obj.image = f"{app.root_path[51:]}\static\images\{save_picture(form.org_image.data)}"

                db.session.commit()
                flash("Your organization information has been successfully updated.", "success")
                return redirect(url_for("account"))
            
            return render_template("orginfo.html", form=form, user_obj=user_obj, page_intro_msg=page_intro_msg)
    
    else:
        flash("You must be an organization administrator to access this page.", "warning")
        return redirect(url_for("home"))

@app.route("/join_organization", methods=["GET", "POST"])
@login_required
def join_organization():
    form = JoinExistingOrganizationForm()
    org_objs = Organization.query.all()

    if request.method == "POST":
        if form.validate_on_submit():
            user_code = form.code.data

            for org in org_objs:
                if str(org.security_code) == str(user_code):
                    current_user.is_organization = True
                    current_user.answered_organization_questions = True
                    current_user.organization_id = org.id
                    list(org.administrators).append(current_user)
                    db.session.commit()

                    flash(f"Your code has matched the following organization: {org.organization_name}. You are now an administrator for that organization.", "success")
                    return redirect(url_for("dashboard"))
                

    return render_template("join_organization.html", form=form)

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    user_organization_obj = None

    if current_user.is_organization == True:
        user_organization_obj = Organization.query.filter_by(id=current_user.organization_id).first()

    if request.method == "GET":
        form.fullname.data = current_user.full_name
        form.email.data = current_user.email

    else:
        if form.validate_on_submit():
            new_user_fullname = form.fullname.data
            new_user_email = form.email.data

            if new_user_email != current_user.email:
                email_check_list = check_email(new_user_email, True)
                new_user_email = email_check_list[1]

                if email_check_list[0] == False:
                    flash("There was an issue with your email. Please try again.", "warning")
                    return redirect(url_for("account"))
            else:
                new_user_email = form.email.data
            
            current_user.full_name = new_user_fullname
            current_user.email = new_user_email
            db.session.commit()
            flash("Your account information has been successfully updated!", "success")
            return redirect(url_for("account"))
        
        if request.form.get("edit_organization_info"):
            flash("You may edit information regarding your organization here.", "info")
            return redirect(url_for("orginfo", user_id=current_user.id))

        if request.form.get("remove_from_organization"):
            current_user.is_organization = False
            current_user.organization_id = None
            current_user.answered_organization_questions = False
            db.session.commit()
            flash(f"You have been successfully removed from {user_organization_obj.organization_name}.", "success")
            return redirect(url_for("account"))
        
        if request.form.get("delete_organization"):
            db.session.delete(user_organization_obj)
            current_user.is_organization = False
            current_user.organization_id = None
            current_user.answered_organization_questions = False
            db.session.commit()
            flash(f"{user_organization_obj.organization_name} has been successsfully deleted.", "success")
            return redirect(url_for("account"))

    if current_user.is_organization and current_user.answered_organization_questions == True:
        return render_template("account.html", form=form, user_organization_obj=user_organization_obj)
    else:
        return render_template("account.html", form=form, user_organization_obj=user_organization_obj)

@app.route("/organizations", methods=["GET", "POST"])
def organizations():
    all_organization_objs = get_all_organization_objs()

    return render_template("organizations.html", all_organization_objs=all_organization_objs, len=len, type=type, list=list)

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if check_organization_status():
        pass

    form = CreateNewPostForm()

    if request.method == "GET":
        current_date = date.today()
        current_date_output = f"{current_date.month}/{current_date.day}/{current_date.year}"
        current_time = datetime.now().strftime("%H:%M")

        return render_template("post.html", form=form, current_date=current_date_output, current_time=current_time)
    
    else:
        if form.event_img.data:
            picture_file = save_picture(form.event_img.data)
            picture_file = f"{app.root_path[51:]}\static\images\{picture_file}"
        else:
            flash("Please provide a valid image that represents your event (image of venue, organization logo, etc.).", "warning")
            return redirect(url_for("post", user_id=current_user.id))
        
        current_post_time = datetime.now().strftime("%I:%M:%S %p")
        current_post_date = date.today().strftime("%b %d, %Y")

        print(form.event_img.data)
        print(picture_file)

        if (request.form.get("post_startdate") == "" or request.form.get("post_startdate") == None) or (request.form.get("post_enddate") == "" or request.form.get("post_enddate") == None) or (request.form.get("post_starttime") == "" or request.form.get("post_starttime") == None) or (request.form.get("post_endtime") == "" or request.form.get("post_endtime") == None):
            flash("Please enter a valid start/end date/time. Try again.", "warning")
            return redirect(url_for("post"))
        elif len(string_to_list(form.keywords.data)) > 6 or len(string_to_list(form.keywords.data)) < 1:
            flash(f"You may enter a max of only 6 keywords. You gave {len(string_to_list(form.keywords.data))}.", "warning")
            return redirect(url_for("post"))
        else:
            new_event = Event(event_name=form.name.data, event_startdate=request.form.get("post_startdate"), event_enddate=request.form.get("post_enddate"), event_starttime=request.form.get("post_starttime"), event_endtime=request.form.get("post_endtime"), event_location=form.location.data, event_max_volunteers=form.max_volunteers.data, event_min_age=form.age_min.data, event_max_age=form.age_max.data, event_category=form.category.data, event_description=form.description.data, event_keywords=form.keywords.data, event_img=picture_file, post_date=current_post_date, post_time=current_post_time, organization_id=current_user.organization_id)
            db.session.add(new_event)
            db.session.commit()
            flash("Event has been successfully posted.", "success")
            return redirect(url_for("view_posts"))

@app.route("/view_posts", methods=["GET", "POST"])
@login_required
def view_posts():
    if check_organization_status():
        pass

    check_for_not_active_events()

    active_events = []
    inactive_events = []
    list_of_keywords_dicts = get_all_keywords_dicts()

    editbtnform = EditPostBtn()
    deletebtnform = DeletePostBtn()

    for i in Event.query.filter_by(organization_id=current_user.organization_id, is_active=True).all():
        active_events.append(i)

    for j in Event.query.filter_by(organization_id=current_user.organization_id, is_active=False).all():
        inactive_events.append(j)

    if request.method == "POST":
        if request.form.get("edit_post_btn"):
            edit_post_id = request.form.get("edit_post_btn")
            return redirect(url_for("edit_post", edit_post_id=edit_post_id))
        if request.form.get("delete_post_btn"):
            delete_post_id = request.form.get("delete_post_btn")
            return redirect(url_for("delete_post", delete_post_id=delete_post_id))

    return render_template("view_posts.html", active_events=active_events, inactive_events=inactive_events, editbtnform=editbtnform, list_of_keywords_dicts=list_of_keywords_dicts, deletebtnform=deletebtnform)

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if check_organization_status():
        pass

    organization_obj = Organization.query.filter_by(id=current_user.organization_id).first()
    all_events = Event.query.filter_by(organization_id=current_user.organization_id).all()
    authorized_admins = organization_obj.administrators

    print(all_events)

    return render_template("dashboard.html", all_events=all_events, authorized_admins=authorized_admins, len=len, organization_obj=organization_obj)

@app.route("/delete_post/<delete_post_id>")
@login_required
def delete_post(delete_post_id):
    if check_organization_status():
        pass

    post_obj = Event.query.filter_by(id=delete_post_id).first()
    db.session.delete(post_obj)
    db.session.commit()

    flash(f"{post_obj.event_name} has been successfully deleted.", "success")
    return redirect(url_for("home"))

@app.route("/edit_post/<edit_post_id>", methods=["GET", "POST"])
@login_required
def edit_post(edit_post_id):
    if check_organization_status():
        pass
    
    form = EditPostForm()
    post_obj = Event.query.filter_by(id=edit_post_id).first()

    if request.method == "GET":
        form.name.data = post_obj.event_name
        post_startdate = post_obj.event_startdate
        post_enddate = post_obj.event_enddate
        post_starttime = post_obj.event_starttime
        post_endtime = post_obj.event_endtime
        form.location.data = post_obj.event_location
        form.max_volunteers.data = post_obj.event_max_volunteers
        form.age_min.data = post_obj.event_min_age
        form.age_max.data = post_obj.event_max_age
        form.category.data = post_obj.event_category
        form.description.data = post_obj.event_description
        form.keywords.data = post_obj.event_keywords
    elif request.method == "POST":
        post_obj.event_name = form.name.data
        post_obj.event_startdate = request.form.get("post_startdate")
        post_obj.event_enddate = request.form.get("post_enddate")
        post_obj.event_starttime = request.form.get("post_starttime")
        post_obj.event_endtime = request.form.get("post_endtime")
        post_obj.event_location = form.location.data
        post_obj.event_max_volunteers = form.max_volunteers.data
        post_obj.event_min_age = form.age_min.data
        post_obj.event_max_age = form.age_max.data
        post_obj.event_category = form.category.data
        post_obj.event_description = form.description.data
        if len(string_to_list(form.keywords.data)) > 6 or len(string_to_list(form.keywords.data)) < 1:
            flash(f"You may enter a max of only 6 keywords. You gave {len(string_to_list(form.keywords.data))}.", "warning")
            return redirect(url_for("post"))
        else:
            post_obj.event_keywords = form.keywords.data

        if form.event_img.data == None:
            post_obj.event_img = post_obj.event_img
        else:
            post_obj.event_img = f"{app.root_path[51:]}\static\images\{save_picture(form.event_img.data)}"

        post_obj.last_updated = str(datetime.now().date().strftime("%b %d, %Y")) + " at " + str(datetime.now().time().strftime("%I:%M:%S %p"))

        db.session.commit()
        
        flash("Post has been successfully updated.", "success")
        return redirect(url_for("view_posts"))

    return render_template("edit_post.html", form=form, post_startdate=post_startdate, post_enddate=post_enddate, post_starttime=post_starttime, post_endtime=post_endtime)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for("home"))

class Client(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    is_organization = db.Column(db.Boolean, default=False)

    full_name = db.Column(db.String(60))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(60))

    answered_organization_questions = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    event_registered_for = db.Column(db.Integer, db.ForeignKey('event.id'))
    
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
    
    registrees = db.relationship("Client", backref="registrees")
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))

    def __repr__(self):
        return f"\n\n{self.event_name}: Organization ID: {self.organization_id}\n\n"

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])

    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    fullname = StringField("Full Name", validators=[InputRequired()])
    email = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired()])

    submit = SubmitField("Register")

class UpdateAccountForm(FlaskForm):
    fullname = StringField("Full Name")
    email = EmailField("Email")

    submit = SubmitField("Save")

class JoinExistingOrganizationForm(FlaskForm):
    code = StringField("Organization Security Code:", validators=[InputRequired()])

    submit = SubmitField("Submit")

class CreateNewPostForm(FlaskForm):
    name = StringField("Event Name:", validators=[InputRequired()])
    startdate = StringField("Event Start Date:", validators=[InputRequired()])
    enddate = StringField("Event End Date:", validators=[InputRequired()])
    starttime = StringField("Event Start Time:", validators=[InputRequired()])
    endtime = StringField("Event End Time:", validators=[InputRequired()])
    location = StringField("Event Location:", validators=[InputRequired()])
    max_volunteers = StringField("Max Number of Volunteers:", validators=[InputRequired()])
    age_min = StringField("Age Range:", validators=[InputRequired()])
    age_max = StringField(None, validators=[InputRequired()])
    category = SelectField("Category:", choices=list(["Pick a category..."] + event_categories))
    description = TextAreaField("Brief Description:", validators=[InputRequired()])
    keywords = StringField("Keywords (each separated by a comma):", validators=[InputRequired()])
    event_img = FileField("Event Image:", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Save")

    def validate_category(category):
        if category.data == "Pick a category...":
            raise ValidationError("Pick a valid category. Please try again.")

class EditPostBtn(FlaskForm):

    editbtn = SubmitField("Edit")

class DeletePostBtn(FlaskForm):

    deletebtn = SubmitField("Delete")

class EditPostForm(FlaskForm):
    name = StringField("Event Name:", validators=[InputRequired()])
    startdate = StringField("Event Start Date:", validators=[InputRequired()])
    enddate = StringField("Event End Date:", validators=[InputRequired()])
    starttime = StringField("Event Start Time:", validators=[InputRequired()])
    endtime = StringField("Event End Time:", validators=[InputRequired()])
    location = StringField("Event Location:", validators=[InputRequired()])
    max_volunteers = StringField("Max Number of Volunteers:", validators=[InputRequired()])
    age_min = StringField("Age Range:", validators=[InputRequired()])
    age_max = StringField(None, validators=[InputRequired()])
    category = SelectField("Category:", choices=list(["Pick a category..."] + event_categories))
    description = TextAreaField("Brief Description:", validators=[InputRequired()])
    keywords = StringField("Keywords (each separated by a comma):", validators=[InputRequired()])
    event_img = FileField("Event Image:", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Save")

    def validate_category(category):
        if category.data == "Pick a category...":
            raise ValidationError("Pick a valid category. Please try again.")

class EventSignUpForm(FlaskForm):

    signup = SubmitField("Sign Up")

class OrganizationInforForm(FlaskForm):
    organization_name = StringField("Name:", validators=[InputRequired()])
    primary_location = StringField("Headquarters Location (city, state):", validators=[InputRequired()])
    mission_statement = TextAreaField("Mission Statement:", validators=[InputRequired()])
    email_contact = StringField("Email:", validators=[InputRequired()])
    phonenumber_contact = StringField("Phone Number:", validators=[InputRequired()])
    website_link = StringField("Link to Website Homepage:", validators=[InputRequired()])
    org_image = FileField("Organization Image:", validators=[FileAllowed(['jpg', 'png']), InputRequired()])

    submit = SubmitField("Save")

def get_random_code(n=6):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + str(f_ext)
    picture_path = os.path.join(app.root_path, 'static\images', picture_fn)
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def get_keywords_dict(list_of_keywords):
    kws_dict = {}
    item_num = 0

    for i in list_of_keywords:
        kws_dict[str(i)] = badge_colors[item_num]
        item_num += 1

    return kws_dict

def get_all_keywords_dicts():
    end_list = []
    
    for e in Event.query.filter_by(organization_id=current_user.organization_id):
        end_list.append(get_keywords_dict(string_to_list(e.event_keywords)))

    return end_list

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

def check_for_not_active_events():
    if current_user.is_authenticated:
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

    list_of_words = list(str(string_of_words).strip("").split(","))

    return list_of_words

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

if __name__ == "__main__":
    app.run(debug=True)

