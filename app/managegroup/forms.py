from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length

# due to a natural defect of wt-form, add non-select check for wt-form selectfield
def myvalidate(form, field):
    if field.data == "--":
        raise ValidationError(
            "Sorry, You have to choose one from the dropdown list.")


class HandleMessageForm(FlaskForm):
    # message = StringField()
    agree = SubmitField('Agree')
    disagree = SubmitField('disAgree')


class AddUserForm(FlaskForm):
    adduser = StringField('Add a user to your group by searching his username:',
                          validators=[DataRequired(), Length(max=32)])
    submit = SubmitField('Confirm change')
# In managegroup()


class DropUserForm(FlaskForm):
    dropuser = SelectField("Delete a user from your group:", validators=[
                           DataRequired()], choices=[])
    submit = SubmitField('Confirm change')
# In managegroup()


class AddGroupForm(FlaskForm):
    # In 'addgroupadm' you input the name of the admin of the group you wanna add into
    addgroupadm = StringField("Apply for adding into a care group by inputing an elderly's username:",
                              validators=[DataRequired(), Length(max=48)])
    submit = SubmitField('Send application')


class LeaveGroupForm(FlaskForm):
    leavegroup = SelectField("Leave an elderly's group:", validators=[
                             DataRequired()], choices=[])
    submit = SubmitField('Confirm change')
