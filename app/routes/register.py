from app import app
from .registerform import RegisterForm
from flask import request, flash, redirect, url_for, render_template
from passlib.hash import sha256_crypt


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
