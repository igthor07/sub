from datetime import datetime
from io import StringIO
import csv

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from sqlalchemy import func

from app.admin.decorators import admin_required
from app.analytics.analytics_engine import AnalyticsEngine
from app.database.models import db, User, Subscription, UsageLog

admin_bp = Blueprint('admin', __name__)
analytics = AnalyticsEngine()


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_subscriptions = Subscription.query.count()
    active_subscriptions = Subscription.query.filter_by(status='Active').count()
    total_usage_records = UsageLog.query.count()
    total_spending = float(
        db.session.query(func.coalesce(func.sum(Subscription.monthly_cost), 0)).filter(
            Subscription.status == 'Active'
        ).scalar() or 0
    )

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_subscriptions = Subscription.query.order_by(Subscription.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        total_usage_records=total_usage_records,
        total_spending=total_spending,
        recent_users=recent_users,
        recent_subscriptions=recent_subscriptions
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )

    pagination = query.order_by(User.id.asc()).paginate(page=page, per_page=per_page, error_out=False)
    users_list = pagination.items

    user_rows = []
    for user in users_list:
        user_rows.append({
            'user': user,
            'subscription_count': Subscription.query.filter_by(user_id=user.id).count()
        })

    return render_template(
        'admin/users.html',
        users=user_rows,
        pagination=pagination,
        search=search
    )


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    subscriptions = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.name.asc()).all()
    usage_logs = UsageLog.query.filter_by(user_id=user.id).order_by(UsageLog.usage_date.desc(), UsageLog.id.desc()).all()

    total_spending = sum(float(sub.monthly_cost or 0) for sub in subscriptions if sub.status == 'Active')
    average_cost = total_spending / len(subscriptions) if subscriptions else 0
    total_hours = sum(float(log.hours_used or 0) for log in usage_logs)

    value_scores = []
    for subscription in subscriptions:
        score = analytics.calculate_value_score(subscription.id, user.id)
        recommendation = 'Keep'
        if score < 40:
            recommendation = 'Review'
        elif score < 60:
            recommendation = 'Consider cancelling'
        value_scores.append({
            'subscription': subscription,
            'score': score,
            'recommendation': recommendation,
            'usage_hours': sum(float(log.hours_used or 0) for log in subscription.usage_logs)
        })

    return render_template(
        'admin/user_detail.html',
        user=user,
        subscriptions=subscriptions,
        usage_logs=usage_logs,
        total_spending=total_spending,
        average_cost=average_cost,
        total_hours=total_hours,
        value_scores=value_scores
    )


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin.user_detail', user_id=user.id))

    user.is_active = not user.is_active
    db.session.commit()
    status_text = 'activated' if user.is_active else 'deactivated'
    flash(f'User account has been {status_text}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'warning')
        return redirect(url_for('admin.user_detail', user_id=user.id))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = Subscription.query.join(User).add_columns(User.username.label('user_name'))
    if search:
        query = query.filter(Subscription.name.ilike(f'%{search}%'))
    if category:
        query = query.filter(Subscription.category == category)
    if status:
        query = query.filter(Subscription.status == status)

    records = query.order_by(Subscription.name.asc()).all()
    categories = db.session.query(Subscription.category).distinct().order_by(Subscription.category.asc()).all()
    categories = [item[0] for item in categories]

    return render_template(
        'admin/subscriptions.html',
        subscriptions=records,
        categories=categories,
        search=search,
        category=category,
        selected_category=category,
        status=status
    )


@admin_bp.route('/subscriptions/<int:subscription_id>')
@login_required
@admin_required
def subscription_detail(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)
    usage_logs = UsageLog.query.filter_by(subscription_id=subscription.id).order_by(UsageLog.usage_date.desc()).all()
    total_hours = sum(float(log.hours_used or 0) for log in usage_logs)
    return render_template('admin/subscriptions.html', subscription=subscription, usage_logs=usage_logs, total_hours=total_hours)


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics_overview():
    total_users = User.query.count()
    new_users = User.query.filter(User.created_at >= datetime.utcnow().replace(day=1)).count()
    active_users = User.query.filter_by(is_active=True).count()
    total_subscriptions = Subscription.query.count()
    active_subscriptions = Subscription.query.filter_by(status='Active').count()
    total_usage_records = UsageLog.query.count()
    total_monthly_spending = float(db.session.query(func.coalesce(func.sum(Subscription.monthly_cost), 0)).filter(Subscription.status == 'Active').scalar() or 0)
    yearly_projection = total_monthly_spending * 12
    average_spending_per_user = total_monthly_spending / total_users if total_users else 0

    category_costs = db.session.query(Subscription.category, func.sum(Subscription.monthly_cost)).filter_by(status='Active').group_by(Subscription.category).all()
    top_subscriptions = db.session.query(Subscription.name, func.sum(UsageLog.hours_used)).join(UsageLog).group_by(Subscription.id, Subscription.name).order_by(func.sum(UsageLog.hours_used).desc()).limit(5).all()

    return render_template(
        'admin/analytics.html',
        total_users=total_users,
        new_users=new_users,
        active_users=active_users,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        total_usage_records=total_usage_records,
        total_monthly_spending=total_monthly_spending,
        yearly_projection=yearly_projection,
        average_spending_per_user=average_spending_per_user,
        category_costs=category_costs,
        top_subscriptions=top_subscriptions
    )


@admin_bp.route('/analytics/spending')
@login_required
@admin_required
def spending_analytics():
    subscriptions = Subscription.query.filter_by(status='Active').order_by(Subscription.monthly_cost.desc()).all()
    total_spending = sum(float(sub.monthly_cost or 0) for sub in subscriptions)
    yearly_projection = total_spending * 12
    category_costs = {}
    for sub in subscriptions:
        category_costs[sub.category] = category_costs.get(sub.category, 0) + float(sub.monthly_cost or 0)

    return render_template(
        'admin/spending.html',
        subscriptions=subscriptions,
        total_spending=total_spending,
        yearly_projection=yearly_projection,
        category_costs=category_costs.items(),
    )


@admin_bp.route('/analytics/usage')
@login_required
@admin_required
def usage_analytics():
    usage_logs = UsageLog.query.order_by(UsageLog.usage_date.desc()).all()
    total_usage = sum(float(log.hours_used or 0) for log in usage_logs)
    usage_by_subscription = db.session.query(Subscription.name, func.sum(UsageLog.hours_used).label('total_hours')).join(UsageLog).group_by(Subscription.id, Subscription.name).order_by(func.sum(UsageLog.hours_used).desc()).all()
    usage_by_category = db.session.query(Subscription.category, func.sum(UsageLog.hours_used).label('total_hours')).join(UsageLog).group_by(Subscription.category).order_by(func.sum(UsageLog.hours_used).desc()).all()

    return render_template(
        'admin/usage.html',
        total_usage=total_usage,
        usage_by_subscription=usage_by_subscription,
        usage_by_category=usage_by_category,
        usage_logs=usage_logs
    )


@admin_bp.route('/analytics/value-score')
@login_required
@admin_required
def value_score_analytics():
    subscriptions = Subscription.query.filter_by(status='Active').all()
    rows = []
    for sub in subscriptions:
        user = User.query.get(sub.user_id)
        score = analytics.calculate_value_score(sub.id, sub.user_id)
        rows.append({
            'subscription': sub.name,
            'user': user.username if user else 'Unknown',
            'cost': float(sub.monthly_cost or 0),
            'usage': sum(float(log.hours_used or 0) for log in sub.usage_logs),
            'value_score': score,
            'recommendation': 'High Value' if score >= 70 else 'Medium Value' if score >= 40 else 'Low Value'
        })
    return render_template('admin/value_score.html', rows=rows)


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    database_status = 'Connected'
    try:
        db.engine.connect().close()
    except Exception:
        database_status = 'Unavailable'

    return render_template(
        'admin/settings.html',
        database_status=database_status,
        admin_username=current_user.username,
        total_users=User.query.count(),
        total_subscriptions=Subscription.query.count(),
        total_usage_records=UsageLog.query.count(),
    )


@admin_bp.route('/reports/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    if report_type == 'users':
        rows = User.query.order_by(User.id).all()
        fieldnames = ['id', 'username', 'email', 'role', 'is_active', 'created_at']
        data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else ''
            } for user in rows
        ]
    elif report_type == 'subscriptions':
        rows = Subscription.query.order_by(Subscription.id).all()
        fieldnames = ['id', 'user_id', 'name', 'category', 'monthly_cost', 'status', 'renewal_date']
        data = [{
            'id': sub.id,
            'user_id': sub.user_id,
            'name': sub.name,
            'category': sub.category,
            'monthly_cost': float(sub.monthly_cost or 0),
            'status': sub.status,
            'renewal_date': sub.renewal_date.isoformat() if sub.renewal_date else ''
        } for sub in rows]
    elif report_type == 'usage':
        rows = UsageLog.query.order_by(UsageLog.id).all()
        fieldnames = ['id', 'user_id', 'subscription_id', 'usage_date', 'hours_used', 'activity_type']
        data = [{
            'id': log.id,
            'user_id': log.user_id,
            'subscription_id': log.subscription_id,
            'usage_date': log.usage_date.isoformat() if log.usage_date else '',
            'hours_used': float(log.hours_used or 0),
            'activity_type': log.activity_type or ''
        } for log in rows]
    elif report_type == 'spending':
        rows = Subscription.query.filter_by(status='Active').order_by(Subscription.monthly_cost.desc()).all()
        fieldnames = ['id', 'user_id', 'name', 'category', 'monthly_cost', 'annual_cost']
        data = [{
            'id': sub.id,
            'user_id': sub.user_id,
            'name': sub.name,
            'category': sub.category,
            'monthly_cost': float(sub.monthly_cost or 0),
            'annual_cost': float(sub.annual_cost or 0) if sub.annual_cost is not None else ''
        } for sub in rows]
    elif report_type == 'value-score':
        rows = Subscription.query.filter_by(status='Active').all()
        fieldnames = ['subscription', 'user', 'monthly_cost', 'usage_hours', 'value_score', 'recommendation']
        data = []
        for sub in rows:
            user = User.query.get(sub.user_id)
            score = analytics.calculate_value_score(sub.id, sub.user_id)
            data.append({
                'subscription': sub.name,
                'user': user.username if user else 'Unknown',
                'monthly_cost': float(sub.monthly_cost or 0),
                'usage_hours': sum(float(log.hours_used or 0) for log in sub.usage_logs),
                'value_score': score,
                'recommendation': 'High Value' if score >= 70 else 'Medium Value' if score >= 40 else 'Low Value'
            })
    else:
        flash('Unknown report type.', 'danger')
        return redirect(url_for('admin.reports'))

    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    response = Response(csv_buffer.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
    return response
