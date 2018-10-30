from flask import render_template, flash, redirect, url_for, request, jsonify, session, logging, g, current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
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

    # define the current group
    current_group = Group.query.filter(Group.groupname == groupname).first_or_404()
    current_cared = current_group.get_admin()
    
    # change the group the user is working on
    if switchGroupForm.validate_on_submit():
        session['group'] = request.form['group']
        flash(f"You are now manipulating on {session['group']}", 'info')
        return redirect(url_for('main.group', groupname=session['group']))

    return render_template('group.html', title='Care Group', user=current_user, group=current_group,
                           cared=current_cared, switchGroupForm=switchGroupForm, addNoteForm=addNoteForm,
                           filterNoteForm=filterNoteForm, notes=notes)
