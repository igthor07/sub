from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from datetime import datetime

from app.database.models import db, User, Subscription, UsageLog
from app.analytics.analytics_engine import AnalyticsEngine


main_bp = Blueprint('main', __name__)

analytics = AnalyticsEngine()


@main_bp.route('/')
@login_required
def dashboard():

    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subscription.name
    ).all()

    total_spending = analytics.calculate_total_spending(
        current_user.id
    )

    active_count = Subscription.query.filter_by(
        user_id=current_user.id,
        status='Active'
    ).count()

    avg_cost_per_use = analytics.calculate_average_cost_per_use(
        current_user.id
    )

    low_utilization = analytics.get_low_utilization_subscriptions(
        current_user.id
    )

    chart_data = analytics.get_dashboard_chart_data(
        current_user.id
    )

    return render_template(
        'main/dashboard.html',
        subscriptions=subscriptions,
        total_spending=total_spending,
        active_count=active_count,
        avg_cost_per_use=avg_cost_per_use,
        low_utilization=low_utilization,
        **chart_data
    )


@main_bp.route('/usage/log', methods=['GET', 'POST'])
@login_required
def usage_log():

    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subscription.name
    ).all()

    if request.method == 'POST':

        subscription_id = request.form.get('subscription_id')
        usage_date = request.form.get('usage_date')
        hours_used = request.form.get('hours_used')
        activity_type = request.form.get('activity_type', '').strip()
        device_used = request.form.get('device_used', '').strip()
        notes = request.form.get('notes', '').strip()

        if not subscription_id or not usage_date or not hours_used:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('main.usage_log'))

        try:
            subscription_id = int(subscription_id)
            usage_date = datetime.strptime(
                usage_date,
                '%Y-%m-%d'
            ).date()
            hours_used = float(hours_used)

        except (ValueError, TypeError):
            flash('Please enter valid usage details.', 'danger')
            return redirect(url_for('main.usage_log'))

        if hours_used < 0:
            flash('Hours used cannot be negative.', 'danger')
            return redirect(url_for('main.usage_log'))

        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=current_user.id
        ).first()

        if not subscription:
            flash('Invalid subscription selected.', 'danger')
            return redirect(url_for('main.usage_log'))

        log = UsageLog(
            user_id=current_user.id,
            subscription_id=subscription_id,
            usage_date=usage_date,
            hours_used=hours_used,
            activity_type=activity_type or None,
            device_used=device_used or None,
            notes=notes or None
        )

        db.session.add(log)
        db.session.commit()

        flash('Usage logged successfully!', 'success')

        return redirect(url_for('main.usage_history'))

    return render_template(
        'usage/log.html',
        subscriptions=subscriptions
    )


@main_bp.route('/usage/history')
@login_required
def usage_history():

    subscription_search = request.args.get(
        'subscription',
        ''
    ).strip()

    activity_type = request.args.get(
        'activity_type',
        ''
    ).strip()

    query = UsageLog.query.filter_by(
        user_id=current_user.id
    )

    if subscription_search:
        query = query.join(
            Subscription
        ).filter(
            Subscription.name.ilike(
                f'%{subscription_search}%'
            )
        )

    if activity_type:
        query = query.filter(
            UsageLog.activity_type == activity_type
        )

    usage_logs = query.order_by(
        UsageLog.usage_date.desc(),
        UsageLog.id.desc()
    ).all()

    total_hours = sum(
        float(log.hours_used or 0)
        for log in usage_logs
    )

    total_logs = len(usage_logs)

    return render_template(
        'usage/history.html',
        usage_logs=usage_logs,
        total_hours=total_hours,
        total_logs=total_logs,
        subscription_search=subscription_search,
        activity_type=activity_type
    )


@main_bp.route(
    '/usage/edit/<int:log_id>',
    methods=['GET', 'POST']
)
@login_required
def edit_usage(log_id):

    log = UsageLog.query.filter_by(
        id=log_id,
        user_id=current_user.id
    ).first_or_404()

    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subscription.name
    ).all()

    if request.method == 'POST':

        subscription_id = request.form.get('subscription_id')
        usage_date = request.form.get('usage_date')
        hours_used = request.form.get('hours_used')
        activity_type = request.form.get(
            'activity_type',
            ''
        ).strip()
        device_used = request.form.get(
            'device_used',
            ''
        ).strip()
        notes = request.form.get(
            'notes',
            ''
        ).strip()

        if (
            not subscription_id
            or not usage_date
            or not hours_used
        ):
            flash(
                'Please fill in all required fields.',
                'danger'
            )
            return redirect(
                url_for(
                    'main.edit_usage',
                    log_id=log.id
                )
            )

        try:
            subscription_id = int(subscription_id)
            hours_used = float(hours_used)
            usage_date = datetime.strptime(
                usage_date,
                '%Y-%m-%d'
            ).date()

        except (ValueError, TypeError):
            flash(
                'Please enter valid usage details.',
                'danger'
            )
            return redirect(
                url_for(
                    'main.edit_usage',
                    log_id=log.id
                )
            )

        if hours_used < 0:
            flash(
                'Hours used cannot be negative.',
                'danger'
            )
            return redirect(
                url_for(
                    'main.edit_usage',
                    log_id=log.id
                )
            )

        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=current_user.id
        ).first()

        if not subscription:
            flash(
                'Invalid subscription selected.',
                'danger'
            )
            return redirect(
                url_for(
                    'main.edit_usage',
                    log_id=log.id
                )
            )

        log.subscription_id = subscription_id
        log.usage_date = usage_date
        log.hours_used = hours_used
        log.activity_type = activity_type or None
        log.device_used = device_used or None
        log.notes = notes or None

        db.session.commit()

        flash(
            'Usage record updated successfully!',
            'success'
        )

        return redirect(
            url_for('main.usage_history')
        )

    return render_template(
        'usage/edit.html',
        log=log,
        subscriptions=subscriptions
    )


@main_bp.route(
    '/usage/delete/<int:log_id>',
    methods=['POST']
)
@login_required
def delete_usage(log_id):

    log = UsageLog.query.filter_by(
        id=log_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(log)
    db.session.commit()

    flash(
        'Usage record deleted successfully!',
        'success'
    )

    return redirect(
        url_for('main.usage_history')
    )


@main_bp.route('/profile')
@login_required
def profile():

    return render_template(
        'profile/settings.html'
    )


@main_bp.route(
    '/profile/update-password',
    methods=['POST']
)
@login_required
def update_password():

    current_password = request.form.get(
        'current_password',
        ''
    )

    new_password = request.form.get(
        'new_password',
        ''
    )

    confirm_password = request.form.get(
        'confirm_password',
        ''
    )

    if not current_user.check_password(
        current_password
    ):
        flash(
            'Current password is incorrect.',
            'danger'
        )
        return redirect(
            url_for('main.profile')
        )

    if len(new_password) < 8:
        flash(
            'New password must be at least 8 characters.',
            'danger'
        )
        return redirect(
            url_for('main.profile')
        )

    if new_password != confirm_password:
        flash(
            'New passwords do not match.',
            'danger'
        )
        return redirect(
            url_for('main.profile')
        )

    current_user.set_password(
        new_password
    )

    db.session.commit()

    flash(
        'Password updated successfully!',
        'success'
    )

    return redirect(
        url_for('main.profile')
    )


@main_bp.route(
    '/profile/update-email',
    methods=['POST']
)
@login_required
def update_email():

    new_email = request.form.get(
        'email',
        ''
    ).strip()

    if not new_email:
        flash(
            'Please enter a valid email address.',
            'danger'
        )
        return redirect(
            url_for('main.profile')
        )

    existing_user = User.query.filter(
        User.email == new_email,
        User.id != current_user.id
    ).first()

    if existing_user:
        flash(
            'This email address is already registered.',
            'danger'
        )
        return redirect(
            url_for('main.profile')
        )

    current_user.email = new_email

    db.session.commit()

    flash(
        'Email address updated successfully!',
        'success'
    )

    return redirect(
        url_for('main.profile')
    )


@main_bp.route(
    '/profile/delete-account',
    methods=['POST']
)
@login_required
def delete_account():

    user = User.query.get(
        current_user.id
    )

    if not user:
        flash(
            'User account not found.',
            'danger'
        )
        return redirect(
            url_for('main.dashboard')
        )

    db.session.delete(user)
    db.session.commit()

    logout_user()

    flash(
        'Your account has been deleted successfully.',
        'success'
    )

    return redirect(
        url_for('auth.login')
    )