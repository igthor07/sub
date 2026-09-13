from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.database.models import db, User


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# =========================
# LOGIN
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)

            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


# =========================
# REGISTER
# =========================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate username
        if not username:
            flash('Username is required.', 'danger')
            return redirect(url_for('auth.register'))

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('auth.register'))

        # Validate email
        if not email:
            flash('Email is required.', 'danger')
            return redirect(url_for('auth.register'))

        # Validate password
        if not password:
            flash('Password is required.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('auth.register'))

        # Confirm password
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        # Check username already exists
        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # Check email already exists
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(
            username=username,
            email=email
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# =========================
# LOGOUT
# =========================
@auth_bp.route('/logout')
@login_required
def logout():

    logout_user()

    flash('You have been logged out.', 'success')

    return redirect(url_for('auth.login'))