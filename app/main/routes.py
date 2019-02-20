from flask import render_template, flash, redirect, url_for, request, jsonify, session, logging, g, current_app
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from sqlalchemy import and_, or_, desc
from datetime import datetime

from app import db
from app.models import *
from app.main import bp
from app.main.forms import *


# @bp.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         g.search_form = SearchForm()
  
# clear all cache in filled form, preventing repeated submit
@bp.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# After login, choose which group to work on
@bp.route('/select_group', methods=['GET', 'POST'])
@login_required
def select_group():
    # If the user is an "elderly", directly direct to his/her default group
    if current_user.usertype == "elderly":
        session['groupname'] = current_user.default_group().groupname
        session['eldername'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().username
        session['elderphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().avatar(26)
        session['adminname'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().username
        session['adminphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().avatar(26)

        flash("Welcome old friend, you are now in your default group", 'info')
        return redirect(url_for('main.group', groupname=session['groupname']))

    switchGroupForm = SwitchGroupForm()
    switchGroupForm.groupname.choices = [(g.groupname, g.groupname) for g in current_user.in_groups()]
    switchGroupForm.groupname.choices.insert(0, ("--", "--"))
    
    # If the user is a "family member/health aide", go the select_group page
    if switchGroupForm.validate_on_submit():
        # request.form['group'] is the cell name from switchGroupForm in main\forms.py
        session['groupname'] = request.form['groupname']
        session['eldername'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().username
        session['elderphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().avatar(26)
        session['adminname'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().username
        session['adminphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().avatar(26)

        flash(f"You are now manipulating on {session['groupname']}", 'info')
        return redirect(url_for('main.group', groupname=session['groupname']))
    
    return render_template('select_group.html', title="Select Group", switchGroupForm=switchGroupForm)


@bp.route('/group/<groupname>', methods=['GET', 'POST'])
@login_required
def group(groupname):
    # define the current group(obj)
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()

    
    # SWITCH GROUP in main page
    switchGroupForm = SwitchGroupForm()
    switchGroupForm.groupname.choices = [(g.groupname, g.groupname) for g in current_user.in_groups()]
    switchGroupForm.groupname.choices.insert(0, ("--", "--"))
    
    # Change the current group you are working on
    # If one view has multiple submit button, don't use "validate_on_submit()",
    #   instead you have to specify which submit button is clicked 
    if switchGroupForm.submitSwitchGroup.data and switchGroupForm.validate():
        # request.form['group'] is the cell name from switchGroupForm in main\forms.py
        session['groupname'] = request.form['groupname']
        session['eldername'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().username
        session['elderphoto'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_elder().avatar(26)
        session['adminname'] = Group.query.filter(
            Group.groupname == session['groupname']).first().get_admin().username
        session['adminphoto'] = Group.query.filter(
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
    if addNoteForm.submitAddNote.data and addNoteForm.validate():
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

    # send a unique tasklist to html
    tasklist = []
    for case in current_group.cases:
        for task in case.tasks:
            tasklist.append(task)
    tasklist = set(tasklist)

    return render_template('group.html', title='Care Group', user=current_user, group=current_group,
                           tasklist=tasklist, switchGroupForm=switchGroupForm,
                           addNoteForm=addNoteForm)


@bp.route('/show_user/<username>')
@login_required
def show_user(username):
    user = User.query.filter(User.username == username).first()
    
    return render_template('show_user.html', title='User Info',
                           user=user)

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


# End editing this note, after elder/admin clicks this button, this note cannot be editted anymore
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
    flash("You have deleted a note", 'success')
    # flash("Note Deleted", 'success')
    return redirect(url_for('main.group', groupname=session['groupname']))


# ------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# Manipulation for Appointment
@bp.route('/add_visit', methods=['GET','POST'])
@login_required
def add_visit():
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()
    
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
    flash("You have deleted an appointment", 'success')
    
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
    form.casename.data = visit.case.casename

    if form.validate_on_submit():
        visit.date = request.form['date']
        visit.time = request.form['time']
        visit.visittext = request.form['visittext']
        visit.case = Case.query.filter(Case.casename==request.form['casename']).first()

        db.session.commit()
        flash('You have edited this visit', 'success')
        return redirect(url_for('main.show_visit', visitid=visitid))
    return render_template('edit_visit.html', title='Edit Visit', visit=visit, form=form)


# ------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# Manipulation for Tasks that the elderly done today
@bp.route('/add_task', methods=["GET", "POST"])
@login_required
def add_task():
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()

    form = TaskForm()
    cases = current_group.cases.filter(Case.endtag != True)
    form.casename.choices = [(c.casename, c.casename) for c in cases]
    form.casename.choices.insert(0, ("--", "--"))
    if form.validate_on_submit():
        timestamp = datetime.utcnow()
        task = Task(tasktext=form.tasktext.data, timestamp=timestamp, user=current_user)
        db.session.add(task)
        
        # find the most recent added task, and link it to selected cases
        thistask = Task.query.order_by(Task.taskid.desc()).first()
        for c in form.casename.data:
            # "c" is the name of the case that will be link to "thistask"
            # "tag" is the Case instance with "tag.casename == c"
            tag = Case.query.filter(Case.casename == c).first()
            thistask.cases.append(tag)
        db.session.commit()
        flash(f"{timestamp}You have recorded a finished task, you can add more finished tasks below or go back to main page", 'success')
        return redirect(url_for('main.add_task'))

    return render_template('add_task.html', title='Add finished tasks', form=form)
