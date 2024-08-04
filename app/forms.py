from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import InputRequired, ValidationError, EqualTo

event_categories = ["Animals/Veterinary", "Religious", "Medical", "Military", "Arts/Literature", "Sports", "Youth/Education", "Nature/Outdoors", "Community", "Philanthropy/General", "Other"]

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])

    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    fullname = StringField("Full Name", validators=[InputRequired()])
    date_of_birth = StringField("Date of Birth", validators=[InputRequired()])
    email = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo("password")])

    submit = SubmitField("Register")

class UpdateAccountForm(FlaskForm):
    fullname = StringField("Full Name")
    email = EmailField("Email")

    submit = SubmitField("Save")

class JoinExistingOrganizationForm(FlaskForm):
    code = PasswordField("Organization Security Code:", validators=[InputRequired()])

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
    
class FilterEventsForm(FlaskForm):
    by_open_search = StringField("By Open Search:")
    by_category = SelectField("By Category:", choices=list(["Pick a category..."] + event_categories))
    by_date = DateField("By Date:")

    save = SubmitField("Save")
