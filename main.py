from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_security import UserMixin, RoleMixin

# ----------------- Configurations --------------------------------

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SECRET_KEY'] = 'dce10f96e430dfc3395fa456fcbaf105456b6cb950953a873067477f17eaf54e'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = "plaintext"
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

db = SQLAlchemy(app)
db.init_app(app)

# ----------------- Extending RegisterForm for register view ----------------------
from flask_security import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired

class ExtendedRegisterForm(RegisterForm):
    username = StringField('Username', [DataRequired()])

# -------------------- Models -------------------------
roles_user = db.Table('roles_user'
, db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
, db.Column('role_id', db.Integer, db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_user, backref=db.backref('users', lazy='dynamic'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255)) 

class Decks(db.Model):
    __tablename__ = 'decks'
    deck_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    score = db.Column(db.String)
    last_reviewed = db.Column(db.DateTime)
    user_decks = db.relationship("User", secondary="user_decks")

class Cards(db.Model):
    __tablename__ = 'cards'
    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    front = db.Column(db.String, nullable=False)
    back = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer)
    count = db.Column(db.Integer)

class UserDecks(db.Model):
    __tablename__ = 'user_decks'
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    deck_id = db.Column(db.Integer,  db.ForeignKey("decks.deck_id"), primary_key=True) 

class DeckCards(db.Model):
    __tablename__ = 'deck_cards'
    deck_id = db.Column(db.Integer,  db.ForeignKey("decks.deck_id"), primary_key=True) 
    card_id = db.Column(db.Integer, db.ForeignKey("cards.card_id"), primary_key=True)

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

from application.api import *
from application.controllers import *

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8080')