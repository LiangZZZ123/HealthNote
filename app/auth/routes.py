from flask import render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import *
from app.models import User, Group
from app.auth.email_password import send_password_reset_email

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():

    current_app.logger.info('here')
    if current_user.is_authenticated:
        return redirect(url_for('group', groupname=current_user.default_group().groupname))
    form = LoginForm()
    if form.validate_on_submit():
        # first() return the user object if exists, or return None, compare to all()
        user = User.query.filter(
            User.username == form.username.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        # if username and password are both right,login that user
        login_user(user)
        # record that user and redirect
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            flash('You have logged in', 'success')
            # need to serialize 'group' object before pass it as instance of Group object,
            # since dont know how to do that, just session pass groupname
            session['groupname'] = current_user.default_group().groupname
            next_page = url_for('main.group', groupname=session['groupname'])
        return redirect(next_page)
        
    return render_template('login.html', title='Login', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # if current_user.is_authenticated:
    #     return redirect(url_for('group', groupname=session['groupname']))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.lower(), email=form.email.data,
                    usertype=form.usertype.data)
        user.set_password(form.password.data)

        # auto-generate group when new user registered
        group = Group(groupname="Group-"+form.username.data.lower(),
                      admin=form.username.data)

        db.session.add(user)
        db.session.add(group)
        db.session.commit()

        # let the registered user join his own gorup
        myuser = User.query.filter(User.username == form.username.data).first()
        mygroup = Group.query.filter(Group.admin == form.username.data).first()
        myuser.join_group(mygroup)
        db.session.commit()

        flash('Registration succeeded, please login now!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.group', groupname=session['groupname']))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/reset_password_do/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.group', groupname=session['groupname']))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('token has expired', 'danger' )
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_do.html', form=form)

