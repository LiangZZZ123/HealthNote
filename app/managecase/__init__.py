from flask import Blueprint

bp = Blueprint('managecase', __name__, template_folder='templates')

from app.managecase import routes