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

    # define the current group(obj)
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()
    
    # change the group the user is working on
    if switchGroupForm.validate_on_submit():
        # request.form['group'] is the cell name from switchGroupForm in main\forms.py
        session['groupname'] = request.form['group']
        session['eldername'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().username
        session['elderphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().avatar(26)
        flash(f"You are now manipulating on {session['groupname']}", 'info')
        return redirect(url_for('main.group', groupname=session['groupname']))

    # ADD NOTES PART
    addNoteForm = AddNoteForm()
    addNoteForm.notetype.choices = [(n.type, n.type) for n in NoteType.query.all()]
    # cases those are closed should not be allowed to be linked to by notes
    cases = current_group.cases.filter(Case.endtag != True)
    addNoteForm.casename.choices = [(c.casename, c.casename) for c in cases]
    addNoteForm.casename.choices.insert(0, ("(Decide later)","(Decide later)"))
    if addNoteForm.validate_on_submit():
        # attention here, dont need to deal with Foreign Key!!!
        thistype = NoteType.query.filter(NoteType.type==addNoteForm.notetype.data).first()
        thiscase = Case.query.filter(Case.casename==addNoteForm.casename.data).first()
        note = Note(notetext=addNoteForm.notetext.data,
                    lasteditor=current_user.username,
                    user=current_user, group=current_group, notetype=thistype,
                    case=thiscase)
        db.session.add(note)
        db.session.commit()
        flash("You have added a note", 'success')
        return redirect(url_for('main.group', groupname=session['groupname']))


    notes = Note.query.filter(Note.groupid == current_group.groupid)

    return render_template('group.html', title='Care Group', user=current_user, group=current_group,
                           notes=notes, switchGroupForm=switchGroupForm,
                           addNoteForm=addNoteForm)


# ------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# Manipulation for Note
@bp.route('/edit_note/<noteid>', methods=["GET", "POST"])
@login_required
def edit_note(noteid):
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()

    note = Note.query.filter(Note.noteid == noteid).first()
    form = AddNoteForm()
    form.notetype.choices = [(n.type, n.type) for n in NoteType.query.all()]
    cases = current_group.cases.filter(Case.endtag != True)
    form.casename.choices = [(c.casename, c.casename) for c in cases]
    form.casename.choices.insert(0, ("(Decide later)","(Decide later)"))

    form.notetype.data = note.notetype.type
    form.notetext.data = note.notetext
    form.casename.data = note.case.casename if note.case != None else "(Decide later)"

    # update that note
    if form.validate_on_submit():
        note.notetype = NoteType.query.filter(NoteType.type==request.form['notetype']).first()
        note.notetext = request.form['notetext']
        note.lasteditor = current_user.username
        note.lastedittime = datetime.utcnow()
        note.case = Case.query.filter(Case.casename==request.form['casename']).first()
        
        db.session.commit()
        flash("You have edited this note", 'success')
        return redirect(url_for('main.group', groupname=session['groupname']))
    return render_template('edit_note.html', title='Edit Note', form=form)


# End editing this note, after admin clicks this button, this note cannot be editted anymore
@bp.route('/end_edit_note/<noteid>', methods=["GET", "POST"])
@login_required
def end_edit_note(noteid):
    note = Note.query.filter(Note.noteid == noteid).first()
    note.endtag = True
    db.session.commit()
    flash("The edit function of this note has been closed", 'success')
    return redirect(url_for('main.group', groupname=session['groupname']))

@bp.route('/delete_note/<noteid>', methods=["POST"])
@login_required
def delete_note(noteid):
    Note.query.filter(Note.noteid == noteid).delete()
    db.session.commit()
    flash("You have deleted a note", 'danger')
    # flash("Note Deleted", 'success')
    return redirect(url_for('main.group', groupname=session['groupname']))


# ------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# Manipulation for Appointment
@bp.route('/add_visit/<groupname>', methods=['GET','POST'])
@login_required
def add_visit(groupname):
    current_group = Group.query.filter(Group.groupname == groupname).first()
    
    form = VisitForm()
    cases = current_group.cases.filter(Case.endtag != True)
    form.casename.choices = [(c.casename, c.casename) for c in cases]
    form.casename.choices.insert(0, ("--","--"))
    if form.validate_on_submit():
        thiscase = Case.query.filter(Case.casename==form.casename.data).first()
        visit = Visit(date=form.date.data,
                      time=form.time.data, visittext=form.visittext.data,
                      group=current_group, case=thiscase)
        db.session.add(visit)
        db.session.commit()
        flash("You have set a new appoinment, remember to arrange your schedule", 'success')
        return redirect(url_for('main.group', groupname=session['groupname']))
    
    return render_template('add_visit.html', title='Add Appointment', form=form)


@bp.route('/delete_visit/<visitid>', methods=["POST"])
@login_required
def delete_visit(visitid):
    Visit.query.filter(Visit.visitid == visitid).delete()
    db.session.commit()
    flash("You have deleted an appointment", 'danger')
    
    return redirect(url_for('main.group', groupname=session['groupname']))

@bp.route('/show_visit/<visitid>')
@login_required
def show_visit(visitid):
    visit = Visit.query.filter(Visit.visitid == visitid).first()
    case = visit.case
    doctor = visit.case.doctors.first()

    return render_template('show_visit.html', title='Appointment Info',
            visit=visit, case=case, doctor=doctor)

@bp.route('/edit_visit/<visitid>', methods=["GET", "POST"])
@login_required
def edit_visit(visitid):
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()

    visit = Visit.query.filter(Visit.visitid == visitid).first()
    form = VisitForm()
    cases = current_group.cases.filter(Case.endtag != True)
    form.casename.choices = [(c.casename, c.casename) for c in cases]
    form.casename.choices.insert(0, ("--", "--"))

    # form.date.data = datetime.strptime(visit.date, '%y-%m-%d').date()
    # form.time.data = visit.time
    form.visittext.data = visit.visittext
    form.casename.data =visit.case.casename

    if form.validate_on_submit():
        visit.date = request.form['date']
        visit.time = request.form['time']
        visit.visittext = request.form['visittext']
        visit.case = Case.query.filter(Case.casename==request.form['casename']).first()

        db.session.commit()
        flash('You have edited this visit', 'success')
        return redirect(url_for('main.show_visit', visitid=visitid))
    return render_template('edit_visit.html', title='Edit Visit', visit=visit, form=form)
