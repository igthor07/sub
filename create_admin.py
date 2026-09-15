from app import create_app
from app.database.models import db, User

app = create_app()


def prompt(prompt_text):
    value = input(f'{prompt_text}: ').strip()
    while not value:
        print('This field is required.')
        value = input(f'{prompt_text}: ').strip()
    return value


with app.app_context():
    name = prompt('Name')
    email = prompt('Email')
    password = prompt('Password')

    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long.')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        raise ValueError('A user with this email already exists.')

    admin_user = User(username=name, email=email, role='admin')
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()

    print(f'Admin account created successfully for {email}.')
