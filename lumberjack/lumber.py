from flask import Flask, render_template, request, redirect, session, request, abort, url_for, g , flash
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from celery import Celery 
from werkzeug.utils import secure_filename

# Flask app -> lumber init
lumber = Flask(__name__)
lumber.config.from_pyfile('config.py')

# Celery init
celery = Celery(lumber.name , broker = lumber.config['CELERY_BROKER_URL'])
celery.conf.update(lumber.config)

# SQLAlchemy init
db = SQLAlchemy(lumber)
engine = create_engine(
    'mysql+mysqldb://root:alpine@127.0.0.1/lumber')
Base = declarative_base()

# Flaks login init
login_manager = LoginManager()
login_manager.init_app(lumber)
login_manager.login_view = 'login'


# Root route
@lumber.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user = current_user.username
    return render_template('base.html', user=user), 200


@lumber.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route for Lumberjack

    """
    form = LoginForm()
    mssg = ""

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)

                return redirect(url_for('index'))
            else:
                return render_template('login.html', subtitle="Login", form=form, error_mssg="Invalid Username or Password")
        else:
            return render_template('login.html', subtitle="Login", form=form, error_mssg="Invalid Username or Password")
    return render_template('login.html', subtitle="Login", form=form, error_mssg=mssg), 200


@lumber.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    user = current_user.username
    form = AddSite()
    upload_folder = "user_data/"+current_user.username 
    tablename = current_user.email
    sql = text("select id,site from `"+tablename+"`")
    result = engine.execute(sql)
    if form.validate_on_submit():
        new_site = form.name.data
        tablename = current_user.email
        sql = text("insert into `"+tablename+"` (site) values('"+new_site+"')")
        result =engine.execute(sql)
        if file not in request.files:
            flash('No file part')
            return redirect(url_for('add')) 
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('add'))
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join( upload_folder , filename))
        return redirect(url_for('add')) 
    return render_template('add.html', subtitle="Add Site",  user=user , form = form , sitelist = result)

@lumber.route('/delete-site/<site>', methods=['GET', 'POST'])
@login_required
def delete_site(site):
    site = site
    print(site)
    tablename = current_user.email
    sql = text("delete from `"+tablename+"` WHERE site='"+site+"'")
    result =engine.execute(sql)           
    return redirect(url_for('add'))

@lumber.route('/insights' ,methods=['GET', 'POST'])
@login_required
def insights():
    user = current_user.username
    return render_template('insights.html' , subtitle = "Insights" ,  user = user)

@lumber.route('/issues' ,methods=['GET', 'POST'])
@login_required
def issues():
    user = current_user.username
    return render_template('issues.html' , subtitle = "Issues" ,  user = user)

@lumber.route('/stream' ,methods=['GET', 'POST'])
@login_required
def stream():
    user = current_user.username
    return render_template('stream.html' , subtitle = "Stream" ,  user = user)



@lumber.route('/signup' , methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    mssg = ""
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            hashed_pass = generate_password_hash(form.password.data , method='sha256')
            new_user = User(username = form.username.data , email = form.email.data , password = hashed_pass)
            user_table = UserTableCreator(form.email.data)
            Base.metadata.create_all(engine)        
            db.session.add(new_user)
            db.session.commit()
            user_dir = "user_data/"+form.username.data+"/"
            ensure_dir(user_dir)
            return redirect(url_for('index'))
        else:
            return render_template('signup.html' , form = form ,subtitle = "Signup" ,error_mssg = "Email already exists.")

    return render_template('signup.html' , subtitle = "Signup" , form = form , error_mssg = mssg),200

@lumber.route('/forgot' , methods=['GET', 'POST'])
def forgot():
    return render_template('login.html' , subtitle = "Forgot"),200


@lumber.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Celery Jobs

# Extra Functions 

def ensure_dir(file_path):
    """
        Takes in file_path and checks for exsisting 
        directory , if not creates one
        INPUT : filepath
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Models 

class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
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

def UserTableCreator(tablename):
    class UserTable(Base):
        __tablename__ = tablename
        id = db.Column(db.Integer , primary_key = True)
        site = db.Column(db.String(80) , default = None)

        def __init__(self, site=None):
            self.site = db.Column(db.String(80))

    return UserTable

class AddSite(FlaskForm):
    name = StringField('name' , validators= [InputRequired()] )
    # Need to check and add more
