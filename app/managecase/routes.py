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

    return render_template('managecase.html', title='Manage Case', group=current_group)

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
        # db.session.commit()

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
            # "item" is the name of the chronic conditon that will be add to "thiscase"
            # "tag" is the Condition instance with "tag.conditiontext == item"
            tag = Condition.query.filter(Condition.conditiontext == item).first()
            thiscase.conditions.append(tag)
        db.session.commit()
        flash("You have created a new case!", 'success')
        return redirect(url_for('managecase.managecase'))
    
    return render_template('addcase.html', title='Add Case', form=form)


@bp.route('/endcase/<caseid>', methods=["GET", "POST"])
@login_required
def endcase(caseid):
    case = Case.query.filter(Case.caseid == caseid).first()
    case.endtag = True
    case.endday = datetime.utcnow()
    db.session.commit()
    flash("This case has been ended !", 'success')
    return redirect(url_for('managecase.managecase'))


@bp.route('/showcase/<caseid>', methods=["GET", "POST"])
@login_required
def showcase(caseid):
    case = Case.query.filter(Case.caseid == caseid).first()

    return render_template('showcase.html', title='Explore this case', case=case)


@bp.route('/editcase/<caseid>', methods=["GET", "POST"])
@login_required
def editcase(caseid):
    case = Case.query.filter(Case.caseid == caseid).first()
    # if we use "obj=" to auto fillin the form, we can use either form.xxx.data
    #   or request.form['xxx']; if form.xxx.data is used for pre-fillin, then we 
    #   can only use request.form['xxx']
    form = EditCaseForm(obj=case, active=False)
    form.casecondition.choices = [(c.conditiontext, c.conditiontext)
                              for c in Condition.query.all()]

    # form.casecondition.data = [c.conditiontext for c in case.conditions]

    # after modify general info of a case, the case will be reactivate 
    if form.validate_on_submit():
        case.casename = request.form['casename']
        case.casetext = request.form['casetext']
        case.endtag=False
        case.endday=None
        
        for tag in case.conditions:
            case.conditions.remove(tag)
        
            # Dont know why "request.form['casecondition']" always give None value???
        for item in form.casecondition.data:
            # "item" is the name of the chronic conditon that will be add to this case
            # "tag" is the instance with the name "item"
            tag = Condition.query.filter(
                Condition.conditiontext == item).first()
            case.conditions.append(tag)

        db.session.commit()
        flash("Your modification has been saved.", 'success')
        return redirect( url_for('managecase.showcase', caseid=caseid) )

    return render_template('editcase.html', title='Edit this case', form=form, caseid=caseid)  


@bp.route('/editdoctor/<caseid>/<doctorid>', methods=["GET", "POST"])
@login_required
def editdoctor(caseid, doctorid):
    doctor = Doctor.query.filter(Doctor.doctorid == doctorid).first()
    form = EditDoctorForm(obj=doctor, active=False)

    if form.validate_on_submit():
        doctor.doctorname=form.doctorname.data
        doctor.phone=form.phone.data
        doctor.specialty=form.specialty.data
        doctor.officename=form.officename.data
        doctor.address1=form.address1.data
        doctor.address2=form.address2.data
        doctor.city=form.city.data
        doctor.zipcode=form.zipcode.data
        
        db.session.commit()
        flash("Your modification has been saved.", 'success')
        return redirect(url_for('managecase.showcase', caseid=caseid))
   
    return render_template('editdoctor.html', title='Edit this doctor', form=form, caseid=caseid)


@bp.route('/editdiary/<caseid>', methods=["GET", "POST"])
def editdiary(caseid):
    case = Case.query.filter(Case.caseid == caseid).first()
    form = EditDiaryForm(obj=case)

    if form.validate_on_submit():
        case.casetext = form.casetext.data

        db.session.commit()
        flash("Your modification has been saved.", 'success')
        return redirect(url_for('managecase.showcase', caseid=caseid))

    return render_template('editdiary.html', title='Edit diary of this case', form=form, caseid=caseid)


@bp.route('/addgoal/<caseid>', methods=["GET", "POST"])
def addgoal(caseid):
    case = Case.query.filter(Case.caseid == caseid).first()
    
    form = AddGoalForm()
    form.goaltype.choices = [(g.type, g.type) for g in GoalType.query.all()]
    form.goaltype.choices.insert(0, ("--","--"))
    if form.validate_on_submit():
        thisgoaltype = GoalType.query.filter(GoalType.type==form.goaltype.data).first()
        goal = Goal(goaltext=form.goaltext.data, starttime=form.starttime.data,
                    case=case, goaltype=thisgoaltype)
        db.session.add(goal)
        db.session.commit()
        flash("A new goal for this case has been added", 'success')
        return redirect(url_for('managecase.showcase', caseid=caseid))
    
    # we can either render 'case(instance)' or 'caseid(an attribute of case)' to html
    return render_template('addgoal.html', title='Add a new goal for this case',
                            form=form, case=case)



@bp.route('/deletegoal/<caseid>/<goalid>', methods=["POST"])
@login_required
def delete_goal(caseid, goalid):
    Goal.query.filter(Goal.goalid==goalid).delete()
    db.session.commit()
    flash("You have deleted a goal for this case", 'success')
    return redirect(url_for('managecase.showcase', caseid=caseid))
