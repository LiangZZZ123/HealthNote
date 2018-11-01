from flask import render_template, flash, redirect, url_for, request, jsonify, session, logging
from flask_login import current_user, login_required
from sqlalchemy import and_, or_, func

from app import db
from app.models import *
from app.managecase import bp
from app.managecase.forms import *

@bp.route('/managecase', methods=['GET', 'POST'])
@login_required
def managecase():
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()
    current_cared = current_group.get_admin()

    form = SwitchCaseForm()
    form.case.choices = [(case.casename, case.casename) for case in current_group.cases.all()]


    return render_template('managecase.html', title='Manage Case', group=current_group,
                cared=current_cared, form=form)

@bp.route('/addcase', methods=['GET', 'POST'])
@login_required
def addcase():
    current_group = Group.query.filter(Group.groupname == session['groupname']).first()

    form = AddCaseForm()
    form.casecondition.choices = [(c.conditiontext, c.conditiontext)
                 for c in Condition.query.all()]

    if form.validate_on_submit():
        case = Case(casename=form.casename.data,
                    casetext=form.casetext.data,
                    endtag=False, group=current_group)
        db.session.add(case)
        db.session.commit()

        thiscase = Case.query.filter(Case.casename == form.casename.data).first()

        # build a "doctor" instance for this case, for many-one relationship with "group"
        #     and "case", use their instance object as parameters
        doctor = Doctor(doctorname=form.doctorname.data, phone=form.phone.data,
                    specialty=form.specialty.data, officename=form.officename.data,
                    address1=form.address1.data, address2=form.address2.data,
                    city=form.city.data, zipcode=form.zipcode.data, 
                    group=current_group, case=thiscase)
        db.session.add(doctor)

        # link this case to chronic conditions been selected
        for item in form.casecondition.data:
            # "item" is the chronic conditon that will be add to this case
            tag = Condition.query.filter(Condition.conditiontext == item).first()
            thiscase.conditions.append(tag)
        db.session.commit()
        flash("You have created a new case!", 'success')
        return redirect(url_for('managecase.managecase'))
    
    return render_template('addcase.html', title='Add Case', form=form)








