from flask import render_template, flash, redirect, url_for, request, jsonify, session, logging, g, current_app
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from sqlalchemy import and_, or_
from datetime import datetime

from app import db
from app.models import *
from app.main import bp
from app.main.forms import *


# @bp.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         g.search_form = SearchForm()
  

@bp.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@bp.route('/group/<groupname>', methods=['GET', 'POST'])
@login_required
def group(groupname):
    # SWITCH GROUP PART
    switchGroupForm = SwitchGroupForm()
    switchGroupForm.group.choices = [(group.groupname, group.groupname) for group in current_user.in_groups().all()]

    # define the current group(obj), current_cared_name(str)
    current_group = Group.query.filter(Group.groupname == groupname).first_or_404()
    current_cared_name = current_group.get_admin()
    
    # change the group the user is working on
    if switchGroupForm.validate_on_submit():
        # request.form['group'] is the cell name from switchGroupForm in main\forms.py
        session['groupname'] = request.form['group']
        flash(f"You are now manipulating on {session['groupname']}", 'info')
        return redirect(url_for('main.group', groupname=session['groupname']))

    # ADD NOTES PART
    addNoteForm = AddNoteForm()
    addNoteForm.notetype.choices = [(n.type, n.type) for n in NoteType.query.all()]
    if addNoteForm.validate_on_submit():
        # attention here, dont need to deal with Foreign Key!!!
        thistype = NoteType.query.filter(NoteType.type==addNoteForm.notetype.data).first()
        note = Note(notetext=addNoteForm.notetext.data,
                    lasteditor=current_user.username, user=current_user,
                    group=current_group, notetype=thistype)
        db.session.add(note)
        db.session.commit()
        flash("You have added a note", 'success')
        return redirect(url_for('main.group', groupname=session['groupname']))


    notes = Note.query.filter(Note.groupid == current_group.groupid)

    return render_template('group.html', title='Care Group', user=current_user, group=current_group,
                           cared=current_cared_name, notes=notes, switchGroupForm=switchGroupForm,
                           addNoteForm=addNoteForm)


# ------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# EDIT / DELETE notes, EDIT doctor, visit
@bp.route('/edit_note/<noteid>', methods=["GET", "POST"])
@login_required
def edit_note(noteid):
    
    note = Note.query.filter(Note.noteid == noteid).first()
    form = AddNoteForm()
    form.notetype.choices = [(n.type, n.type) for n in NoteType.query.all()]
    # why cannot get the type?
    form.notetype.data = note.notetype.type
    form.notetext.data = note.notetext

    # update that note
    if form.validate_on_submit():
        note.notetype = NoteType.query.filter(NoteType.type==request.form['notetype']).first()
        note.notetext = request.form['notetext']
        note.lasteditor = current_user.username
        note.lastedittime = datetime.utcnow()
        
        db.session.commit()
        flash("You have edited this note", 'success')
        return redirect(url_for('main.group', groupname=session['groupname']))
    return render_template('editnote.html', title='Edit Note', form=form)

@bp.route('/delete_note/<noteid>', methods=["POST"])
@login_required
def delete_note(noteid):
    Note.query.filter(Note.noteid == noteid).delete()
    db.session.commit()
    flash("You have deleted a note", 'danger')
    # flash("Note Deleted", 'success')
    return redirect(url_for('main.group', groupname=session['groupname']))


# @bp.route('/delete_doctor/<doctorid>', methods=["POST"])
# @login_required
# def delete_doctor(doctorid):
#     Doctor.query.filter(Doctor.doctorid == doctorid).delete()
#     db.session.commit()
#     flash("You have deleted a doctor", 'danger')
#     return redirect(url_for('main.group', groupname=session['groupname']))


# @bp.route('/delete_visit/<visitid>', methods=["POST"])
# @login_required
# def delete_visit(visitid):
#     Visit.query.filter(Visit.visitid == visitid).delete()
#     db.session.commit()
#     flash("You have deleted an appointment", 'danger')
#     # flash("Note Deleted", 'success')
#     return redirect(url_for('main.group', groupname=session['groupname']))
