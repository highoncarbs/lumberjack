from flask import Flask, render_template, request, redirect, session, request, abort, url_for, g , flash
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length , DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from celery import Celery 
from werkzeug.utils import secure_filename
import json
# Import Spark Engine 
from engine import log_process

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

upload_path = u'/home/Padam/Documents/git/lumberjack/lumberjack/user_data/'

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
    """
    FIXME:  Upload Button icon not visible. 
            File name not showing for uploaded file , fix using BulmaJS            
    """
    user = current_user.username
    form = AddSite()
    upload_folder = upload_path+current_user.username 
    tablename = current_user.email
    sql = text("select id,site_name,data_name from `"+tablename+"`")
    result = engine.execute(sql)

    if form.validate_on_submit() and request.method == 'POST':
        new_site = form.name.data
        tablename = current_user.email

        # Field upload handling 
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('add')) 
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('add'))
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join( upload_folder , filename))

        # Database Insert handling

            sql = text("insert into `"+tablename+"` (site_name , data_name) values('"+new_site+"' , '"+filename+"')")
            result2 =engine.execute(sql)
            
            return redirect(url_for('add')) 
    return render_template('add.html', subtitle="Add Site",  user=user , form = form , sitelist = result)

@lumber.route('/delete-site/<site>', methods=['GET', 'POST'])
@login_required
def delete_site(site):
    """
    FIXME: Delete log files along with site
    """
    site = site
    tablename = current_user.email
    sql = text("delete from `"+tablename+"` WHERE site_name='"+site+"'")
    result =engine.execute(sql)           
    return redirect(url_for('add'))

@lumber.route('/insights' ,methods=['GET', 'POST'])
@login_required
def insights():
    user = current_user.username
    tablename = current_user.email
    sql = text("select site_name from `"+tablename+"`")
    result = engine.execute(sql)
    form = InsightSubmit()

        
    if form.validate_on_submit():
        app_select = request.form.get('application-select')
        sql = text("select data_name , result_name from `"+tablename+"` where site_name = '"+str(app_select)+"'")
        data_file = engine.execute(sql).fetchone()
        data_file = list(data_file)
        
        data_file = data_file[0]
        data_file_path = upload_path+current_user.username+'/'+data_file 
        result_file_path = upload_path+current_user.username+'/'+str(app_select)+'.json'
        
        if os.path.exists(result_file_path) :
            result_file_path = upload_path+current_user.username+'/'+str(app_select)+'.json'
            with open(result_file_path) as data_file:    
                data = json.load(data_file)
                clean_data = []
                for j in data['top_10_pages']:
                    clean_data.append([j['value'] , j['name']])
                top_files = data['top_files']
                top_ip = data['top_ip']
            return render_template('insights.html' , subtitle = "Insights" ,  user = user , sitelist = result , form=form , app_select = app_select , data = clean_data , top_files = top_ip)

        else:

            # Calling Celery task 
            task = log_process(data_file_path , result_file_path)
            try:
                sql = text("insert into `"+tablename+"` (result_name) values('"+str(app_select)+'.txt'+"') where site_name = '"+app_select+"'")
                result3 =engine.execute(sql)
            except Exception:
                print('Unable to save result path into database')

            return render_template('insights.html' , subtitle = "Insights" ,  user = user , sitelist = result , form=form , app_select = app_select , data = data_file)
    return render_template('insights.html' , subtitle = "Insights" ,  user = user , sitelist = result , form = form)

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
        print('Ohhh')

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
        site_name = db.Column(db.String(80) , default = None)
        data_name = db.Column(db.String(80) , default = None)
        result_name = db.Column(db.String(80) , default = None)
        def __init__(self, site=None):
            self.site = db.Column(db.String(80))

    return UserTable

class AddSite(FlaskForm):
    name = StringField('name' , validators= [InputRequired()] )
    # Need to check and add more

class InsightSubmit(FlaskForm):
    # form_name = HiddenField('Form Name')
    # select_temp = SelectField('applications' , validators = [DataRequired()])
    pass