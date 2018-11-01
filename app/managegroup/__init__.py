from flask import Blueprint

bp = Blueprint('managegroup', __name__, template_folder='templates')

from app.managegroup import routes