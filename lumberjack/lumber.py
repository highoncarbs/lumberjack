from flask import Flask , render_template , request , redirect , session , request , abort , url_for ,g
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , UserMixin , login_user , login_required , logout_user,current_user
from flask_wtf import FlaskForm
from wtforms import StringField , PasswordField 
from wtforms.validators import InputRequired , Email , Length
from werkzeug.security import generate_password_hash , check_password_hash
# import models.user

# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import create_engine
# import config

lumber = Flask(__name__)		
lumber.config.from_pyfile('config.py')

db = SQLAlchemy(lumber)

login_manager = LoginManager()
login_manager.init_app(lumber)
login_manager.login_view = 'login'

@lumber.route('/' , methods=['GET', 'POST'])
@login_required
def index():
	user = current_user.username
	return render_template('base.html' , user = user),200


@lumber.route('/login' , methods=['GET', 'POST'])
def login():
	form = LoginForm()
	mssg = ""

	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user:
			if check_password_hash(user.password , form.password.data):
				login_user(user)
				return redirect(url_for('index'))
			else:
				return render_template('login.html' , subtitle = "Login",form = form ,error_mssg = "Invalid Username or Password")	
		else:
			return render_template('login.html' ,subtitle = "Login", form = form ,error_mssg = "Invalid Username or Password")	
	return render_template('login.html' , subtitle = "Login" , form = form , error_mssg = mssg),200

@lumber.route('/dash' ,methods=['GET', 'POST'])
@login_required
def dash():
	user = current_user.username
	return user

@lumber.route('/signup' , methods=['GET', 'POST'])
def signup():
	form = SignupForm()
	mssg = ""
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user is None:
			hashed_pass = generate_password_hash(form.password.data , method='sha256')
			new_user = User(username = form.username.data , email = form.email.data , password = hashed_pass)
			db.session.add(new_user)
			db.session.commit()
			return redirect(url_for('index'))
		else:
			return render_template('signup.html' , form = form ,subtitle = "Signup" ,error_mssg = "Email already exists.")

	return render_template('signup.html' , subtitle = "Signup" , form = form , error_mssg = mssg),200

@lumber.route('/forgot' , methods=['GET', 'POST'])
def forgot():
	return render_template('login.html' , subtitle = "Signup"),200

@lumber.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))



@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    email = StringField('email', validators=[
                           InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])


class SignupForm(FlaskForm):
    username = StringField('username', validators=[
                           InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired(), Email(
        message="Invalid Email"), Length(max=50)])

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
