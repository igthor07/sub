from getpass import getpass

from app import create_app
from app.database.models import db, User


app = create_app()

with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()

    if admin is None:
        raise SystemExit('Admin account admin@example.com was not found.')

    password = getpass('New admin password (minimum 8 characters): ')
    if len(password) < 8:
        raise SystemExit('Password must be at least 8 characters long.')

    confirmation = getpass('Confirm new admin password: ')
    if password != confirmation:
        raise SystemExit('Passwords do not match.')

    admin.set_password(password)
    admin.role = 'admin'
    admin.is_active = True
    db.session.commit()

    print('Admin password reset successfully.')