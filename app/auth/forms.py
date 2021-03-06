from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, EqualTo, Length
from app.models import User


# due to a natural defect of wt-form, add non-select check for wt-form selectfield
def myvalidate(form, field):
    if field.data == "--":
        raise ValidationError(
            "Sorry, You have to choose one from the dropdown list.")


class LoginForm(FlaskForm):
    # "DataRequired" validator checks that the field is not submitted empty.
    username = StringField('Username', validators=[DataRequired(),Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(),Length(max=20)])
    # remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),Length(max=32)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=64)])
    usertype = SelectField('UserType',  validators=[DataRequired(),myvalidate], 
                choices=[('--', '--'), ('elderly', 'elderly'), ('family member', 'family member'),
                ('home health aide','home health aide')], default='--')
    password = PasswordField('Password', validators=[DataRequired(), Length(max=20)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # ensure the username and emailAddress using is not yet in database
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('User name exists, please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email address exists, please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField('Request Password Reset')
