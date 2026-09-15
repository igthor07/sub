from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


def ensure_database_schema():
    """Add missing columns to existing databases without breaking current data."""
    try:
        inspector = db.inspect(db.engine)
    except Exception:
        return

    if 'users' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('users')}

    if 'role' not in columns:
        try:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
            )
        except Exception:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
            )

    if 'is_active' not in columns:
        try:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
            )
        except Exception:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
            )

    db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default='user',
        server_default='user'
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='1'
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    subscriptions = db.relationship(
        'Subscription',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    usage_logs = db.relationship(
        'UsageLog',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    @property
    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    monthly_cost = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    annual_cost = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    billing_cycle = db.Column(
        db.String(20),
        nullable=False,
        default='Monthly'
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    renewal_date = db.Column(
        db.Date,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default='Active'
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    usage_logs = db.relationship(
        'UsageLog',
        backref='subscription',
        lazy=True,
        cascade='all, delete-orphan'
    )


class UsageLog(db.Model):
    __tablename__ = 'usage_logs'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    subscription_id = db.Column(
        db.Integer,
        db.ForeignKey('subscriptions.id'),
        nullable=False
    )

    usage_date = db.Column(
        db.Date,
        nullable=False
    )

    hours_used = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    activity_type = db.Column(
        db.String(50),
        nullable=True
    )

    device_used = db.Column(
        db.String(50),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )