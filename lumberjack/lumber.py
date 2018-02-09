from flask import Flask , render_template , request

lumber = Flask(__name__)

@lumber.route('/')
def index():
	return render_template('base.html'),200


@lumber.route('/register')
def register():
	return render_template('base_login.html'),200
