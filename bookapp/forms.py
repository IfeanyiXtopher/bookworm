from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired

from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import Email, DataRequired,EqualTo,Length

class RegForm(FlaskForm):
    fullname = StringField("First Name",validators=[DataRequired("First Name cannot be empty")])
    email = StringField("Email Address",validators=[Email(message="invalid email format"),])
    pwd = PasswordField("Enter Password",validators=[DataRequired()])
    confpwd = PasswordField("Confirm Password",validators=[EqualTo('pwd', message=("password must be the same"))])
    btnsubmit = SubmitField("Register!")

class DpForm(FlaskForm):
    dp = FileField("Upload a Profile Picture", validators=[FileRequired(), FileAllowed(['jpg','png','jpeg'])])
    btnupload = SubmitField("Upload Picture")

class ProfileForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired("First Name cannot be empty")])
    btnsubmit = SubmitField("Update Profile")

class ContactForm(FlaskForm):
    email = StringField("Email",validators=[Email(message="invalid email format")])
    btnsubmit = SubmitField("Subscribe")

# class DonationForm(FlaskForm):
#     fullname = StringField("FullName",validators=[DataRequired()])
#     email = StringField("Email",validators=[DataRequired()])
#     amt = StringField("Amount",validators=[DataRequired()])
#     btnsubmit = SubmitField("Donate!")