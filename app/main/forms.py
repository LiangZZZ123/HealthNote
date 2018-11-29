from flask import request
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField, SelectMultipleField, DateTimeField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User

# due to a natural defect of wt-form, add non-select check for wt-form selectfield
def myvalidate(form, field):
    if field.data == "--":
        raise ValidationError("Sorry, You have to choose one from the dropdown list.")


class SwitchGroupForm(FlaskForm):
    groupname = SelectField("Switch group: ",
                        validators=[DataRequired(), myvalidate], choices=[], default='--')
    submitSwitchGroup = SubmitField('Confirm')


class AddNoteForm(FlaskForm):
    notetype = SelectField('Nature of note', validators=[DataRequired(), myvalidate],
                           choices=[], default='--')
    casename = SelectField('Link this note to a CASE',  validators=[DataRequired(), myvalidate],
                           choices=[], default='(Decide later)')
    notetext = TextAreaField('Text of note', validators=[Length(min=1)])
    submitAddNote = SubmitField('Confirm')


class VisitForm(FlaskForm):
    casename = SelectField('Link this appointment to a CASE',  validators=[DataRequired(), myvalidate],
                           choices=[], default='--')
    date = DateField("Appointment date(format: 2018-01-01)")
    time = TimeField("Appointment time(format: 7:30 AM)")
    visittext = TextAreaField("Memo(Maximum 500 chars)", validators=[Length(max=500)])
    submit = SubmitField('Confirm')


class TaskForm(FlaskForm):
    # "casename" field is for linking one task to multiple cases
    casename = SelectMultipleField(
        "Select cases that this task should be linked to(Press CTRL for multi-selection)",
        validators=[DataRequired(), myvalidate], choices=[], default='--')
    tasktext = TextAreaField("Describe this task you've just done(Maximum 250 chars)", validators=[Length(max=250)])
    submit = SubmitField('Confirm')