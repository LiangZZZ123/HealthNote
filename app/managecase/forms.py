from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, TextAreaField, DateTimeField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import Case, Doctor
from datetime import datetime

# due to a natural defect of wt-form, add non-select check for wt-form selectfield
def myvalidate(form, field):
    if field.data == "--":
        raise ValidationError(
            "Sorry, You have to choose one from the dropdown list.")

# when you create a case, you create a doctor, you can just give a name to doctor, 
    # and leave other info blank
class AddCaseForm(FlaskForm):
    casename = StringField("Name of the case(EG: Leg injury from Nov.20 with Doctor Smith)",
        validators=[Length(min=5, max=120)])
    # 'caseconditon' is for building many-many relationship with Condition table
    casecondition = SelectMultipleField("Select chronic conditions for this field(Press CTRL for multi-selection)",
                        validators=[DataRequired()], choices=[])
    casetext = TextAreaField("For your case diary(Maximum 2000 chars)", validators=[
                             Length(min=5, max=2000)])
    
    doctorname = StringField("Doctor name", validators=[Length(min=2, max=20)])
    phone = StringField("Phone", validators=[ Length(max=10)])
    specialty = StringField("Specialty", validators=[ Length(max=64)])
    officename = StringField("Office name", validators=[ Length(max=64)])
    address1 = StringField("Address1", validators=[ Length(max=128)])
    address2 = StringField("Address2", validators=[ Length(max=64)])
    city = StringField("City", validators=[ Length(max=30)])
    zipcode = StringField("Zip", validators=[ Length(max=5)])
    
    submit = SubmitField('Create Case')

    def validate_casename(self, casename):
        case = Case.query.filter(Case.casename==casename.data).first()
        if case is not None:
            raise ValidationError('Please use a different case name.')

    def validate_doctorname(self, doctorname):
        doctor = Doctor.query.filter(Doctor.doctorname==doctorname.data).first()
        if doctor is not None:
            raise ValidationError('Please use a different doctor name.')

class EditCaseForm(FlaskForm):
    casename = StringField("Name of the case(EG: Leg injury from Nov.20 with Doctor Smith)",
        validators=[Length(min=5, max=120)])
    # 'caseconditon' is for building many-many relationship with Condition table
    casecondition = SelectMultipleField("Select chronic conditions for this field(Press CTRL for multi-selection)",
                        validators=[DataRequired()], choices=[])
    casetext = TextAreaField("For your case diary(Maximum 2000 chars)", validators=[Length(min=5, max=2000)])
    
    submit = SubmitField('Confirm')

class EditDiaryForm(FlaskForm):
    casetext = TextAreaField("For your case diary(Maximum 2000 chars)", validators=[Length(min=5, max=2000)])
    submit = SubmitField('Confirm')

class AddGoalForm(FlaskForm):
    goaltype = SelectField("Select a type for this goal", validators=[DataRequired(), myvalidate],
                           choices=[], default='--')
    goaltext = TextAreaField("Describe this goal in short words(Maximum 250 chars)", validators=[
                             Length(min=5, max=250)])
    starttime = DateTimeField(
        "Input the start time for this goal(Format 2018-11-11 20:00:00)", default=datetime.utcnow())
    
    submit = SubmitField('Confirm')

class EditDoctorForm(FlaskForm):
    doctorname = StringField("Doctor name", validators=[DataRequired(), Length(max=20)])
    phone = StringField("Phone", validators=[Length(min=10, max=10)])
    specialty = StringField("Specialty", validators=[DataRequired(), Length(max=64)])
    officename = StringField("Office name", validators=[DataRequired(), Length(max=64)])
    address1 = StringField("Address1", validators=[DataRequired(), Length(max=128)])
    address2 = StringField("Address2", validators=[Length(max=64)])
    city = StringField("City", validators=[DataRequired(), Length(max=30)])
    zipcode = StringField("Zip", validators=[Length(min=5, max=5)])

    submit = SubmitField('Confirm')

