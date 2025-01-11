from flask import redirect, url_for, render_template, request, flash, jsonify
from app import app, db, session
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt

from models.models import User

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from flask import request, render_template, redirect, url_for, flash

from flask import flash, jsonify


@app.before_request
def require_login():
    # Allow access to certain public routes
    public_routes = ['login', 'register', 'static', 'admin_login']
    if request.endpoint not in public_routes and not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.path.startswith('/admin/'):
        if current_user.is_authenticated and current_user.role != 1:  # Assuming role 1 is admin
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('home'))  # Redirect to home or another page


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('pos'))  # Redirect to a different page if the user is already logged in

    if request.method == 'GET':
        return render_template('front/auth/register.html')

    elif request.method == 'POST':
        form = request.get_json()

        # Check if the email already exists
        existing_user = User.query.filter_by(email=form.get('email')).first()
        if existing_user:
            flash("Email already in use. Please choose a different email.", "error")
            return jsonify({
                "redirect": url_for('register')  # Send redirect URL back to frontend
            }), 400

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.get('password')).decode('utf-8')

        # Concatenate first name and last name
        name = form.get('first_name') + ' ' + form.get('last_name')

        # Create new user object
        user = User(
            name=name,
            email=form.get('email'),
            password=hashed_password,
            gender=0,
            role=0,  # Default to user role
            status=1  # Default to active
        )

        # Save the user to the database
        db.session.add(user)
        db.session.commit()

        flash("User registered successfully! Please log in.", "success")
        return jsonify({
            "redirect": url_for('login')  # Send redirect URL back to frontend
        }), 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pos'))  # Redirect to a different page if the user is already logged in

    print("Current session data:", session)
    if request.method == 'GET':
        return render_template('front/auth/login.html')
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        # Check if the email exists
        if not user:
            flash('Invalid email. Please try again.', 'danger')
            return redirect(url_for('login'))

        # Check if the password is correct
        if not bcrypt.check_password_hash(user.password, password):
            flash('Invalid password. Please try again.', 'danger')
            return redirect(url_for('login', email=email))

        # Check if the user is inactive
        if user.status == 0:
            flash('Account is inactive. Please contact admin.', 'warning')
            return redirect(url_for('login'))

        # Login the user if everything is correct
        login_user(user)
        print("Authenticated user:", current_user)
        print("User ID:", current_user.id)
        print("User email:", current_user.email)
        flash(f'Login successful!\nWelcome {current_user.name}!', 'success')  # Flash success message
        return redirect(url_for('pos'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 1:  # If already an admin
        return redirect(url_for('dashboard'))  # Redirect to admin dashboard

    if request.method == 'GET':
        return render_template('admin/auth/login.html')  # Admin login page
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'danger')
            return redirect(url_for('admin_login'))

        user = User.query.filter_by(email=email).first()

        # Check if the email exists
        if not user or user.role != 1:  # Admin role is 1
            flash('Unauthorized email detected!.', 'danger')
            return redirect(url_for('admin_login', email=email))

        # Check if the password is correct
        if not bcrypt.check_password_hash(user.password, password):
            flash('Invalid password. Try again.', 'danger')
            return redirect(url_for('admin_login', email=email))

        # Check if the user is inactive
        if user.status == 0:
            flash('Account is inactive.', 'warning')
            return redirect(url_for('admin_login', email=email))

        # Login the admin user
        login_user(user)
        flash(f'Login successful!\nWelcome {current_user.name}!', 'success')
        return redirect(url_for('dashboard'))  # Redirect to admin dashboard after login


@app.route('/logout')
def logout():
    session.pop('_flashes', None)
    if current_user.role == 1:  # Assuming role 1 is admin
        logout_user()  # Logs out the current admin
        flash('Logged out successfully.', 'success')
        return redirect(
            url_for('admin_login'))  # Redirect to the admin login page for security reasons, not the home page.
    else:  # Assuming it a user
        logout_user()  # Logs out the current user
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('login'))  # Redirect to the login page


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
