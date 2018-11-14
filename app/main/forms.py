from flask import request
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User

# due to a natural defect of wt-form, add non-select check for wt-form selectfield
def myvalidate(form, field):
    if field.data == "--":
        raise ValidationError("Sorry, You have to choose one from the dropdown list.")


class SwitchGroupForm(FlaskForm):
    group = SelectField("Switch group(default is your own's)",
                        validators=[DataRequired()], choices=[])
    submit = SubmitField('Confirm')


class AddNoteForm(FlaskForm):
    notetype = SelectField('Nature of note',  validators=[DataRequired(), myvalidate],
                           choices=[], default='--')
    casename = SelectField('Link this note to a CASE',  validators=[DataRequired(), myvalidate],
                           choices=[], default='(Decide later)')
    notetext = TextAreaField('Text of note', validators=[Length(min=1)])
    submit = SubmitField('Confirm')


class VisitForm(FlaskForm):
    casename = SelectField('Link this appointment to a CASE',  validators=[DataRequired(), myvalidate],
                           choices=[], default='--')
    date = DateField("Appointment date(format: 2018-01-01)")
    time = TimeField("Appointment time(format: 7:30 AM)")
    visittext= StringField("Memo")
    submit = SubmitField('Confirm')


# class DoctorForm(FlaskForm):
#     doctorname = StringField("Doctor name", validators=[
#                              DataRequired(), Length(max=20)])
#     phone = StringField("Phone", validators=[Length(min=10, max=10)])
#     specialty = StringField("Specialty", validators=[
#                             DataRequired(), Length(max=64)])
#     officename = StringField("Office name", validators=[
#                              DataRequired(), Length(max=64)])
#     address1 = StringField("Address1", validators=[
#                            DataRequired(), Length(max=128)])
#     address2 = StringField("Address2", validators=[
#                            DataRequired(), Length(max=64)])
#     city = StringField("City", validators=[DataRequired(), Length(max=30)])
#     zipcode = StringField("Zip", validators=[Length(min=5, max=5)])
#     submit = SubmitField('Confirm')