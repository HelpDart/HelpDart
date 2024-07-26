from app import app, db, Serializer
from app.models import Client, Organization, Event
from app.forms import LoginForm, RegisterForm, UpdateAccountForm, JoinExistingOrganizationForm, CreateNewPostForm, EditPostBtn, DeletePostBtn, EditPostForm, EventSignUpForm, OrganizationInforForm
from app.funcs import check_organization_status, check_age, check_max_participants_reached, get_random_code, save_picture, get_keywords_dict, check_email, email_unique, check_password, get_is_organization_value, get_all_organization_objs, encrypt_password, get_all_emails, check_for_not_active_events, string_to_list, send_authentication_email, check_authenticated_email
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from datetime import date, datetime
import bcrypt
from itsdangerous import SignatureExpired, BadTimeSignature


@app.route("/", methods=["GET", "POST"])    
@app.route("/home", methods=["GET", "POST"])
def home():
    check_for_not_active_events()
    all_events = Event.query.filter_by(is_active=True).all()
    sign_up_form = EventSignUpForm()
    if request.method == "POST":
        if check_authenticated_email():
            pass
        if request.form.get("signupforeventbtn"):
            event_obj = Event.query.filter_by(id=int(request.form.get("signupforeventbtn"))).first()
            dob_worked = check_age(current_user.date_of_birth, event_obj)
            max_not_reached = check_max_participants_reached(event_obj)
            if dob_worked and max_not_reached:
                list(event_obj.registrees).append(current_user)
                # if current_user.event_registered_for == None:
                #     current_user.event_registered_for = str(list(event_obj.id))
                # else:
                #     current_user.event_registered_for = str(list(current_user.event_registered_for).append(str(event_obj.id)))
                db.session.commit()
                flash(f"You have been successfully signed up for {event_obj.event_name}!", "success")
                return redirect(url_for("home"))
            else:
                if dob_worked == False:
                    flash(f"You do not meet the age requirment for this event. You must be between {event_obj.event_min_age} to {event_obj.event_max_age}.", "warning")
                    return redirect(url_for("home"))
                else:
                    flash(f"Sorry, the maximum capacity for this event has been reached.", "warning")
                    return redirect(url_for("home"))
        if request.form.get("removefromeventbtn"):
            event_obj = Event.query.filter_by(id=int(request.form.get("removefromeventbtn"))).first()
            list(event_obj.registrees).remove(current_user)
            db.session.commit()
            flash(f"You have been successfully removed from {event_obj.event_name}!", "success")
            return redirect(url_for("home"))

    return render_template("home.html", all_events=all_events, sign_up_form=sign_up_form, Organization=Organization, len=len, int=int)

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
        user_fullname = form.fullname.data
        user_email = form.email.data
        user_dob = str(datetime(int(request.form.get("dob")[0:4]), int(request.form.get("dob")[5:7]), int(request.form.get("dob")[8:])))[0:10]
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
        elif datetime(int(user_dob[0:4]), int(user_dob[5:7]), int(user_dob[8:])) > datetime(int(str(date.today())[0:4]), int(str(date.today())[5:7]), int(str(date.today())[8:])):
            flash("That is an invalid date of birth. Please try again.", "warning")
            return redirect(url_for("register"))
        else:
            new_user = Client(is_organization=user_is_organization, is_confirmed=False, full_name=user_fullname, date_of_birth=user_dob, email=user_email, password=encrypt_password(user_password))
            db.session.add(new_user)
            db.session.commit()

            token = str(Serializer.dumps(user_email, salt="email-confirmation"))
            send_authentication_email(user_email, token)

            flash("You have been sent an email to activate your account. Please check your email and follow the link provided.", "primary")
            return redirect(url_for("home"))

    return render_template("register.html", form=form)

@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = Serializer.loads(token, salt="email-confirmation", max_age=300)
    except (SignatureExpired, BadTimeSignature):
        flash("Your security token has expired or was incorrect. Please try again.", "info")
        return redirect(url_for("register"))
    user_obj = Client.query.filter_by(email=email).first()
    user_obj.is_confirmed = True
    db.session.commit()
    login_user(user_obj)
    flash(f"Welcome, {current_user.email}. You have been successfully logged in!", "success")
    return redirect(url_for("home"))

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

                    if check_authenticated_email():
                        pass

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
                if check_authenticated_email():
                    pass
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

@app.route("/send_confirmation_email", methods=["GET", "POST"])
@login_required
def send_confirmation_email():
    if current_user.is_confirmed == False:
        token = str(Serializer.dumps(current_user.email, salt="email-confirmation"))
        send_authentication_email(current_user.email, token)
        flash("Your account has not been activated yet. An email has just been sent to you to activate your account.", "primary")
        return redirect(url_for("account"))
    else:
        flash("Your email has already been confirmed.", "primary")
        return redirect(url_for("home"))

@app.route("/join_organization", methods=["GET", "POST"])
@login_required
def join_organization():
    form = JoinExistingOrganizationForm()
    org_objs = Organization.query.all()

    if request.method == "POST":
        if form.validate_on_submit():

            if check_authenticated_email():
                pass
            
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
                else:
                    flash(f"That code did not match any organizations currently in our database. Please try again or contact your organization.", "warning")
                    return redirect(url_for("join_organization"))

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

    elif request.method == "POST":
        
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
            if check_authenticated_email():
                pass
            flash("You may edit information regarding your organization here.", "info")
            return redirect(url_for("orginfo", user_id=current_user.id))
        
        if request.form.get("remove_from_organization"):
            if check_authenticated_email():
                pass
            current_user.is_organization = False
            current_user.organization_id = None
            current_user.answered_organization_questions = False
            db.session.commit()
            flash(f"You have been successfully removed from {user_organization_obj.organization_name}.", "success")
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
    
    elif request.method == "POST":
        if check_authenticated_email():
            pass
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
            new_event = Event(event_name=form.name.data, event_startdate=request.form.get("post_startdate"), event_enddate=request.form.get("post_enddate"), event_starttime=request.form.get("post_starttime"), event_endtime=request.form.get("post_endtime"), event_location=form.location.data, event_max_volunteers=form.max_volunteers.data, event_min_age=form.age_min.data, event_max_age=form.age_max.data, event_category=form.category.data, event_description=form.description.data, event_keywords=str(get_keywords_dict(string_to_list(form.keywords.data))), event_img=picture_file, post_date=current_post_date, post_time=current_post_time, organization_id=current_user.organization_id)
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

    editbtnform = EditPostBtn()
    deletebtnform = DeletePostBtn()

    for i in Event.query.filter_by(organization_id=current_user.organization_id, is_active=True).all():
        active_events.append(i)

    for j in Event.query.filter_by(organization_id=current_user.organization_id, is_active=False).all():
        inactive_events.append(j)

    if request.method == "POST":
        if check_authenticated_email():
            pass
        if request.form.get("edit_post_btn"):
            edit_post_id = request.form.get("edit_post_btn")
            return redirect(url_for("edit_post", edit_post_id=edit_post_id))
        if request.form.get("delete_post_btn"):
            delete_post_id = request.form.get("delete_post_btn")
            return redirect(url_for("delete_post", delete_post_id=delete_post_id))
        if request.form.get("delete_from_history"):
            delete_post_id = request.form.get("delete_from_history")
            return redirect(url_for("delete_post", delete_post_id=delete_post_id))

    return render_template("view_posts.html", active_events=active_events, inactive_events=inactive_events, editbtnform=editbtnform, deletebtnform=deletebtnform, list=list, dict=dict)

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if check_authenticated_email():
        pass
    if check_organization_status():
        pass

    organization_obj = Organization.query.filter_by(id=current_user.organization_id).first()
    all_events = Event.query.filter_by(organization_id=current_user.organization_id).all()
    authorized_admins = organization_obj.administrators

    return render_template("dashboard.html", all_events=all_events, authorized_admins=authorized_admins, len=len, organization_obj=organization_obj)

@app.route("/delete_post/<delete_post_id>")
@login_required
def delete_post(delete_post_id):
    if check_authenticated_email():
        pass
    if check_organization_status():
        pass

    post_obj = Event.query.filter_by(id=delete_post_id).first()
    db.session.delete(post_obj)
    db.session.commit()

    flash(f"{post_obj.event_name} has been successfully deleted.", "success")
    return redirect(url_for("view_posts"))

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
        if check_authenticated_email():
            pass
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
            post_obj.event_keywords = str(get_keywords_dict(string_to_list(form.keywords.data)))

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