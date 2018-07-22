from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Pastumbers'
app.config['MYSQL_DB'] = 'BBOnline'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#OLD MYSQL PASSWORD: lookinlikeasnacc

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Index
@app.route('/')
def index():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')

#Articles
@app.route('/users')
@is_logged_in
def users():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get users
    result = cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    #get logged in user
    result = cur.execute("SELECT * FROM users WHERE username=%s", [session['username']])

    loggedInUser = cur.fetchone()

    if result > 0:
        return render_template('users.html', users=users, loggedInUser=loggedInUser)
    else:
        msg = 'No Users Found'
        return render_template('users.html', msg=msg)

    # Close connection
    cur.close()

#Single User
@app.route('/user/<string:id>')
def user(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM users WHERE id=%s", (id))

    user = cur.fetchone()

    return render_template('user.html', user=user)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to DB

        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('you are now registered and can log in', 'success')

        return redirect(url_for('index'))

        # return render_template('register.html', form=form)
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    #Get bucks
    result = cur.execute("SELECT * FROM users WHERE username=%s", [session['username']])
    user = cur.fetchone()
    userID = int(user['id'])
    # print(str(type(userID))+ str(userID) + " <---------- <------ USERID")

    # Get bucks given to user
    result = cur.execute("SELECT users.name FROM users INNER JOIN bucktransfers ON bucktransfers.getterID=users.id WHERE bucktransfers.giverid=%s", [userID])
    bucksYouGave = cur.fetchall()

    result = cur.execute("SELECT users.name FROM users INNER JOIN bucktransfers ON bucktransfers.giverID=users.id WHERE bucktransfers.getterid=%s",[userID])
    bucksYouGot = cur.fetchall()

    return render_template('dashboard.html', user=user, bucksYouGot=bucksYouGot, bucksYouGave=bucksYouGave)

    #Close connection
    cur.close()

@app.route('/add_buck/<string:id>')
@is_logged_in
def add_buck(id):
    # Create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users WHERE id=%s", (id))
    gettingUser = cur.fetchone()
    result = cur.execute("SELECT * FROM users WHERE username=%s", [session['username']])
    givingUser = cur.fetchone()
    if gettingUser.get('username') != session['username'] and int(givingUser['bucksToGive']) > 0:\
        #give/take bucks
        cur.execute("UPDATE users SET bucks = bucks + 1 WHERE id = %s", (id))
        cur.execute("UPDATE users SET bucksToGive = bucksToGive - 1 WHERE username = %s", [session['username']])

        #add transfer to transfer table
        giverID = int(givingUser['id'])
        cur.execute("INSERT INTO bucktransfers VALUES(%s,%s)", (giverID,id))
    else:
        if gettingUser.get('username') == session['username']:
            flash('You cant give yourself bucks you cheater', 'success')
        if int(givingUser['bucksToGive']) <= 0:
            flash(r"You don't have any more bucks to give", 'success')

    # Commit to DB
    mysql.connection.commit()

    # Close Conection
    cur.close()

    return redirect(url_for('users'))

if __name__ == '__main__':
    app.secret_key='secret123'


    #Serving Options
        # 1) serve locally with live edits
    app.run(debug=True)

        # 2) serve over http, no live edits
    # app.run(ssl_context='adhoc')

    # HOW TO INSTALL MYSQL:
        # 1) pip install mysql
        # 2) install mysql server from windows mysql installer

    # HOW TO DISPLAY SNACC.ME USERS
        # 1) USE snaccme;
        # 2) SELECT * FROM users;

    #DELETE A USER
        # 1) DELETE FROM users WHERE variable=value;

# GIVE MYSELF BUCKS: UPDATE users SET bucksToGive = 10 WHERE id = 1;

# #Register Form Class
# class ArticleForm(Form):
#     title = StringField('Title', [validators.Length(min=1, max=200)])
#     body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
# @app.route('/add_article', methods=['GET', 'POST'])
# @is_logged_in
# def add_article():
#     form = ArticleForm(request.form)
#     if request.method == 'POST' and form.validate():
#         title = form.title.data
#         body = form.body.data
#
#         #Create cursor
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))
#
#         #commit to DB
#         mysql.connection.commit()
#
#         #Close connection
#         cur.close()
#
#         flash('Article Created', 'success')
#
#         return redirect(url_for('dashboard'))
#
#     return render_template('add_article.html', form=form)

# Edit Article
# @app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
# @is_logged_in
# def edit_article(id):
#     # Create cursor
#     cur = mysql.connection.cursor()
#
#     #get article by id
#     result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
#
#     article = cur.fetchone()
#
#     #Get form
#     form = ArticleForm(request.form)
#
#     #populate fields
#     form.title.data = article['title']
#     form.body.data = article['body']
#
#     if request.method == 'POST' and form.validate():
#         title = request.form['title']
#         body = request.form['body']
#
#         #Create cursor
#         cur = mysql.connection.cursor()
#         cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title ,body, id))
#
#         #commit to DB
#         mysql.connection.commit()
#
#         #Close connection
#         cur.close()
#
#         flash('Article Updated', 'success')
#
#         return redirect(url_for('dashboard'))
#
#     return render_template('edit_article.html', form=form)

# @app.route('/delete_article/<string:id>', methods=['POST'])
# @is_logged_in
# def delete_article(id):
#     #Create cursor
#     cur = mysql.connection.cursor()
#
#     #execute
#     cur.execute("DELETE FROM articles WHERE id=%s", [id])
#
#     #Commit to DB
#     mysql.connection.commit()
#
#     #Close connection
#     return redirect(url_for('dashboard'))
#