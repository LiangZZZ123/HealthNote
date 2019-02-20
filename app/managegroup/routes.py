from flask import render_template, flash, redirect, url_for, request, jsonify, session, logging
from flask_login import current_user, login_required
from sqlalchemy import and_, or_, func

from app import db
from app.models import *
from app.managegroup import bp
from app.managegroup.forms import *


@bp.route('/managegroup', methods=['GET', 'POST'])
@login_required
def managegroup():
    handleMessageForm = HandleMessageForm()
    addUserForm = AddUserForm()
    dropUserForm = DropUserForm()
    leaveGroupForm = LeaveGroupForm()
    addGroupForm = AddGroupForm()

    if current_user.usertype == "elderly":
        dropUserForm.dropuser.choices = [
            (user.username, user.username) for user in current_user.users_in_mygroup().all()]
    
    leaveGroupForm.leavegroup.choices = [
        (group.groupname, group.groupname) for group in current_user.in_groups().all()]

    # add user to your default group
    if addUserForm.validate_on_submit():
        userToAdd = User.query.filter(
            User.username == func.lower(addUserForm.adduser.data)).first()
        if userToAdd and userToAdd not in current_user.default_group().users:
            current_user.default_group().add_member(userToAdd)
            db.session.commit()
            flash(
                f'New member {addUserForm.adduser.data} has been successfully added to your group', 'success')
            return redirect(url_for("managegroup.managegroup"))
        else:
            flash('User not found, or you have already added him/her', 'warning')

    # drop user from your default group
    if dropUserForm.validate_on_submit():
        userToDrop = User.query.filter(
            User.username == dropUserForm.dropuser.data).first()
        if (userToDrop and userToDrop != current_user):
            current_user.default_group().drop_member(userToDrop)
            db.session.commit()
            flash(
                f'User {dropUserForm.dropuser.data} has been successfully removed from your group', 'success')
            return redirect(url_for("managegroup.managegroup"))
        else:
            flash(
                "Please choose a user to remove, and you cannot remove yourself", 'warning')

    # send application for adding into a group
    if addGroupForm.validate_on_submit():
        userToSendTo = User.query.filter(
            User.username == func.lower(addGroupForm.addgroupadm.data)).first()
        groupToAdd = Group.query.filter(
            Group.groupid == userToSendTo.default_group().groupid).first()

        if (groupToAdd and groupToAdd not in current_user.groups):
            # avoid the same application to be sent twice
            message = Message.query.filter(and_(
                Message.messagesender == current_user.userid,
                Message.messagetype == 'addgroup',
                Message.userid == userToSendTo.userid
            )).first()
            if not message:
                message = Message(messagetype="addgroup", messagesender=current_user.userid,
                                  messagetext=f"{current_user.username.capitalize()}({current_user.usertype.capitalize()}) applied to add to your care group!",
                                  user=userToSendTo)
                # userToSendTo.messages.append(message)
                db.session.commit()
                flash('Application has been sent!', 'success')
                return redirect(url_for("managegroup.managegroup"))
            else:
                flash(
                    "Your application is on process, please don't send the same application again!", 'warning')
        else:
            flash("No such elderly, or you are already in his/her care group.", 'warning')

    # leave group(must not leave user's default group)
    if leaveGroupForm.validate_on_submit():
        groupToLeave = Group.query.filter(
            Group.groupname == leaveGroupForm.leavegroup.data).first()
        if (groupToLeave and groupToLeave != current_user.default_group()):
            current_user.leave_group(groupToLeave)
            db.session.commit()
            flash(
                f'You have successfully left group {leaveGroupForm.leavegroup.data}', 'success')
            if (session['groupname'] == groupToLeave.groupname):
                return redirect(url_for("main.select_group"))
            else:
                return redirect(url_for("managegroup.managegroup"))
        else:
            flash(
                'Please choose a group, and you cannot leave your default group', 'warning')

    return render_template('managegroup.html', title='Manage Group', group=session,
        addUserForm=addUserForm, dropUserForm=dropUserForm,
        addGroupForm=addGroupForm, leaveGroupForm=leaveGroupForm,
        handleMessageForm=handleMessageForm)


# if "Agree" button in managegroup is clicked
@bp.route('/agreemessage/<messageid>', methods=["POST"])
@login_required
def agreemessage(messageid):
    # deal with messages received(including "add group request")
    # 'message' is the message to dispose this time, 'sender' is the user who sent this message
    thismessage = Message.query.filter(Message.messageid == messageid).first()
    sender = User.query.filter(
        User.userid == thismessage.messagesender).first()

    if thismessage.messagetype == 'addgroup':
        # execute "Add applier to the group"
        current_user.default_group().add_member(sender)
        # delete "message" from message box
        Message.query.filter(Message.userid == current_user.userid).delete()
        db.session.commit()
        flash(
            f'New member {sender.username} has been successfully added to your group', 'success')
        return(redirect(url_for("managegroup.managegroup")))


# if "Disagree" button in managegroup is clicked
@bp.route('/disagreemessage/<messageid>', methods=["POST"])
@login_required
def disagreemessage(messageid):
    thismessage = Message.query.filter(Message.messageid == messageid).first()

    if thismessage.messagetype == 'addgroup':
        Message.query.filter(Message.userid == current_user.userid).delete()
        db.session.commit()
        return(redirect(url_for("managegroup.managegroup")))
