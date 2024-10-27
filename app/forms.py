from app.funcs import unique_phonenumber
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import ValidationError, EqualTo, DataRequired
import phonenumbers

event_categories = ["Animals/Veterinary", "Religious", "Medical", "Military", "Arts/Literature", "Sports", "Youth/Education", "Nature/Outdoors", "Community", "Philanthropy/General", "Other"]

class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])

    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    fullname = StringField("Full Name:", validators=[DataRequired()])
    date_of_birth = StringField("Date of Birth:", validators=[DataRequired()])
    email = EmailField("Email:", validators=[DataRequired()])
    phonenumber = StringField("Phone Number:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password:", validators=[DataRequired(), EqualTo("password")])
    profile_picture = FileField("Profile Picture (optional):", validators=[FileAllowed(['jpg', 'png'])])

    def validate_phonenumber(form, phonenumber):
        if len(phonenumber.data) > 16 or unique_phonenumber(phonenumber.data):
            raise ValidationError('Invalid phone number.')
        try:
            input_number = phonenumbers.parse(phonenumber.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')
        except:
            input_number = phonenumbers.parse("+1"+phonenumber.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')

    submit = SubmitField("Register")

class UpdateAccountForm(FlaskForm): 
    fullname = StringField("Full Name:")
    email = EmailField("Email:")
    dob = DateField("Date of Birth:")
    profile_picture = FileField("Profile Picture:", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Save")

class JoinExistingOrganizationForm(FlaskForm):
    code = PasswordField("Organization Security Code:", validators=[DataRequired()])

    submit = SubmitField("Submit")

class CreateNewPostForm(FlaskForm):
    name = StringField("Event Name:", validators=[DataRequired()])
    startdate = StringField("Event Start Date:", validators=[DataRequired()])
    enddate = StringField("Event End Date:", validators=[DataRequired()])
    starttime = StringField("Event Start Time:", validators=[DataRequired()])
    endtime = StringField("Event End Time:", validators=[DataRequired()])
    location = StringField("Event Location:", validators=[DataRequired()])
    max_volunteers = StringField("Max Number of Volunteers:", validators=[DataRequired()])
    age_min = StringField("Age Range:", validators=[DataRequired()])
    age_max = StringField(None, validators=[DataRequired()])
    category = SelectField("Category:", choices=list(["Pick a category..."] + event_categories))
    description = TextAreaField("Brief Description:", validators=[DataRequired()])
    keywords = StringField("Keywords (each separated by a comma):", validators=[DataRequired()])
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
    name = StringField("Event Name:", validators=[DataRequired()])
    startdate = StringField("Event Start Date:", validators=[DataRequired()])
    enddate = StringField("Event End Date:", validators=[DataRequired()])
    starttime = StringField("Event Start Time:", validators=[DataRequired()])
    endtime = StringField("Event End Time:", validators=[DataRequired()])
    location = StringField("Event Location:", validators=[DataRequired()])
    max_volunteers = StringField("Max Number of Volunteers:", validators=[DataRequired()])
    age_min = StringField("Age Range:", validators=[DataRequired()])
    age_max = StringField(None, validators=[DataRequired()])
    category = SelectField("Category:", choices=list(["Pick a category..."] + event_categories))
    description = TextAreaField("Brief Description:", validators=[DataRequired()])
    keywords = StringField("Keywords (each separated by a comma):", validators=[DataRequired()])
    event_img = FileField("Event Image:", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Save")

    def validate_category(category):
        if category.data == "Pick a category...":
            raise ValidationError("Pick a valid category. Please try again.")

class EventSignUpForm(FlaskForm):

    signup = SubmitField("Sign Up")

class OrganizationInforForm(FlaskForm):
    organization_name = StringField("Name:", validators=[DataRequired()])
    primary_location = StringField("Headquarters Location (city, state):", validators=[DataRequired()])
    mission_statement = TextAreaField("Mission Statement:", validators=[DataRequired()])
    email_contact = StringField("Email:", validators=[DataRequired()])
    phonenumber_contact = StringField("Phone Number:", validators=[DataRequired()])
    website_link = StringField("Link to Website Homepage:", validators=[DataRequired()])
    org_image = FileField("Organization Image:", validators=[FileAllowed(['jpg', 'png']), DataRequired()])

    submit = SubmitField("Save")
    
class FilterEventsForm(FlaskForm):
    by_open_search = StringField("By Open Search:")
    by_category = SelectField("By Category:", choices=list(["Pick a category..."] + event_categories))
    by_date = DateField("By Date:")

    save = SubmitField("Save")

class UserEmergencyContactForm(FlaskForm):
    emergency_contact_full_name = StringField("Emergency Contact Name:", validators=[DataRequired()])
    emergency_contact_email = StringField("Emergency Contact Email:", validators=[DataRequired()])
    emergency_contact_phonenumber = StringField("Emergency Contact Phone Number:", validators=[DataRequired()])
    emergency_contact_relation = StringField("Emergency Contact's Relation to You:", validators=[DataRequired()])

    save = SubmitField("Save")
