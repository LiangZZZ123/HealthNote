# Define sql OEM syntax, do any SQL table creation/alternation in this file
# format: table name are captalized
from datetime import datetime, date
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index

# This class is to be inherited by models that need fulltext search function
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)



# Flask-Login user loader function
@login.user_loader
def load_user(userid):
    return User.query.get(int(userid))


# "group_has_user" is an association table, for add how many people to your group
# "groups" is the relationship() on User side, for that user added by how many groups
# "users" is the relationship() on Group side, for that group has how many users
# 'user_id' includes all users,  'group_id' includes all groups
# use "following.c.follower_id" to access
# ---Attention: in windows10 mysql, all table names aren't captalized!!!---
group_has_user = db.Table('group_has_user',
                    db.Column('userid', db.Integer, db.ForeignKey('user.userid')),
                    db.Column('groupid', db.Integer, db.ForeignKey('group.groupid'))
                    )

# integrate userControl and UserDbManagement into User class


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    usertype = db.Column(db.String(64))
    realname = db.Column(db.String(64))
    # many-many with class Group, a dict that store groups(type:objects) a user is in
    groups = db.relationship('Group', secondary=group_has_user, back_populates="users",
                             lazy='dynamic')
    # one-many with class Note, Message, Tasks
    notes = db.relationship('Note', back_populates="user", lazy='dynamic')
    messages = db.relationship('Message', back_populates="user", lazy='dynamic')
    tasks = db.relationship('Task', back_populates="user", lazy='dynamic')

    # build the picture for user
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    # override get_id function in UserMixin
    def get_id(self):
        return self.userid

    # format the printing result of objects in User class
    def __repr__(self):
        return '<User {}'.format(self.username)

    # password hashing and verification
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # User.userid is passed by token to protect the reset password process
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.userid, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            userid = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(userid)

    # return the default group of current_user
    def default_group(self):
        group_default = (Group.query.filter(
            Group.elder == self.username).first())
        return group_default

    # since all join_group is invited by admin, so no need to check if_ingroup first
    def join_group(self, group):
        self.groups.append(group)

    # a user leaves a group
    def leave_group(self, group):
        self.groups.remove(group)

    def in_groups(self):
        groups_in = (Group.query
                     .join(group_has_user, (Group.groupid == group_has_user.c.groupid))
                     .filter(group_has_user.c.userid == self.userid)
                     )
        return groups_in

    def users_in_mygroup(self):
        mygroup_users = (User.query
                         .join(group_has_user, (User.userid == group_has_user.c.userid))
                         .filter(group_has_user.c.groupid == self.default_group().groupid)
                         )
        return mygroup_users


class Message(db.Model):
    __tablename__ = 'message'
    messageid = db.Column(db.Integer, primary_key=True)
    messagetype = db.Column(db.String(32))
    messagetext = db.Column(db.String(256))
    # use user.userid for messagesender
    messagesender = db.Column(db.Integer)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))

    user = db.relationship('User', back_populates='messages')


class Group(db.Model):
    __tablename__ = 'group'
    groupid = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(64), index=True, unique=True)
    elder = db.Column(db.String(64), index=True, unique=True)
    admin = db.Column(db.String(64))
    # many-many with class User
    users = db.relationship('User', secondary=group_has_user,
                            back_populates='groups', lazy='dynamic')
    # one-many with class Visit,Doctor,Note,Case
    visits = db.relationship('Visit', back_populates='group', lazy='dynamic')
    doctors = db.relationship('Doctor', back_populates='group', lazy='dynamic')
    notes = db.relationship('Note', back_populates='group', lazy='dynamic')
    cases = db.relationship('Case', back_populates='group', lazy='dynamic')

    # user doing manipulation on his default group
    def isjoined_user(self, user):
        return(self.users.filter(group_has_user.c.userid == user.userid)).count() > 0

    def add_member(self, user):
        if not self.isjoined_user(user):
            self.users.append(user)

    def drop_member(self, user):
        if self.isjoined_user(user):
            self.users.remove(user)

    def get_elder(self):
        elder = User.query.filter(self.elder == User.username).first()
        return(elder)

    def get_admin(self):
        admin = User.query.filter(self.admin == User.username).first()
        return(admin)



class Note(SearchableMixin, db.Model):
    __tablename__ = 'note'
    __searchable__ = ['notetext']
    noteid = db.Column(db.Integer, primary_key=True)
    notetext = db.Column(db.String(2048))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    endtag = db.Column(db.Boolean)
    lasteditor = db.Column(db.String(64))
    lastedittime = db.Column(db.DateTime, default=datetime.utcnow)

    caseid = db.Column(db.Integer, db.ForeignKey('case.caseid'))
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    groupid = db.Column(db.Integer, db.ForeignKey('group.groupid'))
    notetypeid = db.Column(db.Integer, db.ForeignKey('notetype.notetypeid'))

    case = db.relationship('Case', back_populates='notes')
    user = db.relationship('User', back_populates='notes')
    group = db.relationship('Group', back_populates='notes')
    notetype = db.relationship('NoteType', back_populates='notes')

class NoteType(db.Model):
    __tablename__ = 'notetype'
    notetypeid = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(128))

    notes = db.relationship('Note', back_populates='notetype', lazy='dynamic')


class Visit(db.Model):
    __tablename__ = 'visit'
    visitid = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(64))
    time = db.Column(db.String(64))
    visittext = db.Column(db.String(512))
    
    groupid = db.Column(db.Integer, db.ForeignKey('group.groupid'))
    caseid = db.Column(db.Integer, db.ForeignKey('case.caseid'))

    group = db.relationship('Group', back_populates='visits')
    case = db.relationship('Case', back_populates='visits')


class Doctor(db.Model):
    __tablename__ = 'doctor'
    doctorid = db.Column(db.Integer, primary_key=True)
    doctorname = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(64))
    specialty = db.Column(db.String(64))
    officename = db.Column(db.String(64))
    address1 = db.Column(db.String(128))
    address2 = db.Column(db.String(64))
    city = db.Column(db.String(64))
    zipcode = db.Column(db.String(32))

    groupid = db.Column(db.Integer, db.ForeignKey('group.groupid'))
    caseid = db.Column(db.Integer, db.ForeignKey('case.caseid'))

    group = db.relationship('Group', back_populates='doctors')
    case = db.relationship('Case', back_populates='doctors')

    def doctors_in_thisgroup(thisgroup):
        thisgroup_doctors = Doctor.query.filter(
            Doctor.groupid == thisgroup.groupid)
        return thisgroup_doctors


# ------------------------------------------------------------------------------
# Association tables for case-condition, case-task
case_has_condition = db.Table('case_has_condition',
                    db.Column('caseid', db.Integer, db.ForeignKey('case.caseid')),
                    db.Column('conditionid', db.Integer, db.ForeignKey('condition.conditionid'))
                    )

case_has_task = db.Table('case_has_task',
                    db.Column('caseid', db.Integer, db.ForeignKey('case.caseid')),
                    db.Column('taskid', db.Integer, db.ForeignKey('task.taskid'))
                    )

class Case(db.Model):
    __tablename__ ='case'   
    caseid = db.Column(db.Integer, primary_key=True)
    casename = db.Column(db.String(128), unique=True, index=True)
    casetext = db.Column(db.String(2048))
    startday = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    endday = db.Column(db.DateTime, index=True)
    endtag = db.Column(db.Boolean)

    # many-one with class Group
    groupid = db.Column(db.Integer, db.ForeignKey('group.groupid'))    

    group = db.relationship('Group', back_populates='cases')

    # one-many with class Visit,Doctor,Note,Goal
    visits = db.relationship('Visit', back_populates='case', lazy='dynamic')
    doctors = db.relationship('Doctor', back_populates='case', lazy='dynamic')
    notes = db.relationship('Note', back_populates='case', lazy='dynamic')
    goals = db.relationship('Goal', back_populates='case', lazy='dynamic')

    # many-many with class Condition, Task
    conditions = db.relationship('Condition', secondary=case_has_condition, 
                                back_populates="cases", lazy='dynamic')
    tasks = db.relationship('Task', secondary=case_has_task, 
                                back_populates="cases", lazy='dynamic')
                                


class Condition(db.Model):
    __tablename__ = 'condition'
    conditionid = db.Column(db.Integer, primary_key=True)
    conditiontext = db.Column(db.String(128))

    # many-many with class Case
    cases = db.relationship('Case', secondary=case_has_condition,
                                 back_populates="conditions", lazy='dynamic')


class Task(db.Model):
    __tablename__ = 'task'
    taskid = db.Column(db.Integer, primary_key=True)
    tasktext = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # many-one with class User
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))

    user = db.relationship('User', back_populates='tasks')

    # many-many with class Case
    cases = db.relationship('Case', secondary=case_has_task,
                            back_populates="tasks", lazy='dynamic')


class Goal(db.Model):
    __tablename__ = 'goal'
    goalid = db.Column(db.Integer, primary_key=True)
    goaltext = db.Column(db.String(256))
    starttime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # many-one with class Case, GoalType
    caseid = db.Column(db.Integer, db.ForeignKey('case.caseid'))
    goaltypeid = db.Column(db.Integer, db.ForeignKey('goaltype.goaltypeid'))
    
    case = db.relationship('Case', back_populates='goals')
    goaltype = db.relationship('GoalType', back_populates='goals')


class GoalType(db.Model):
    __tablename__ = 'goaltype'
    goaltypeid = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64))

    goals = db.relationship('Goal', back_populates='goaltype', lazy='dynamic')
