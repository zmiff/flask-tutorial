import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

#REGISTER
#when flask recieves request to this route it will call the register function
@bp.route('/register', methods=('GET', 'POST'))
def register():
    #if the user submitted the form request method will be POST and start validating the form
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        #query db and check to see if the user already exists in db
        elif db.execute(
            #database library will take care of escaping characters before inserting to db
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            #save changes
            db.commit()
            return redirect(url_for('auth.login'))
            #if validation fails flash the error(s)
        flash(error)

    #render register.html
    return render_template('auth/register.html')

#LOGIN
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        #check hashed password vs stored password and securely compares them
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            #clear session
            session.clear()
            #sequrely store the users id in session and available in subsequent request
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    #render login.html
    return render_template('auth/login.html')

#LOAD THE USER
#this will run before the view function no matter what url is requested
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    #check if user_id is stored in session
    if user_id is None:
        g.user = None
    else:
        #if stored get the user from db and store in g.user
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

#LOGOUT
@bp.route('/logout')
def logout():
    #destroy session
    session.clear()
    #redirect to index url_for('index') will render the view @app.route('/hello')
    return redirect(url_for('index'))

##DECORATOR CHECK IF LOGGED IN ELSE REDIRECT TO LOGIN (can be applied to vievs)
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
