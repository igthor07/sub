from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.database.models import Subscription, UsageLog
from app.analytics.analytics_engine import AnalyticsEngine


analytics_bp = Blueprint(
    'analytics',
    __name__,
    url_prefix='/analytics'
)

analytics = AnalyticsEngine()


# =========================================================
# COST ANALYSIS
# =========================================================
@analytics_bp.route('/cost-analysis')
@login_required
def cost_analysis():

    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        status='Active'
    ).order_by(
        Subscription.monthly_cost.desc()
    ).all()

    # -----------------------------------------------------
    # TOTAL MONTHLY COST
    # -----------------------------------------------------
    total_monthly = sum(
        float(subscription.monthly_cost or 0)
        for subscription in subscriptions
    )

    # -----------------------------------------------------
    # TOTAL ANNUAL COST
    # -----------------------------------------------------
    total_annual = sum(
        float(subscription.annual_cost)
        if subscription.annual_cost is not None
        else float(subscription.monthly_cost or 0) * 12
        for subscription in subscriptions
    )

    # -----------------------------------------------------
    # COST BY CATEGORY
    # -----------------------------------------------------
    category_costs = {}

    for subscription in subscriptions:

        category = subscription.category or 'Other'

        category_costs[category] = (
            category_costs.get(category, 0)
            + float(subscription.monthly_cost or 0)
        )

    chart_labels = list(
        category_costs.keys()
    )

    chart_values = list(
        category_costs.values()
    )

    return render_template(
        'analytics/cost_analysis.html',
        subscriptions=subscriptions,
        total_monthly=round(total_monthly, 2),
        total_annual=round(total_annual, 2),
        chart_labels=chart_labels,
        chart_values=chart_values
    )


# =========================================================
# USAGE ANALYSIS
# =========================================================
@analytics_bp.route('/usage-analysis')
@login_required
def usage_analysis():

    usage_logs = UsageLog.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UsageLog.usage_date.desc()
    ).all()

    # -----------------------------------------------------
    # TOTAL HOURS
    # -----------------------------------------------------
    total_hours = sum(
        float(log.hours_used or 0)
        for log in usage_logs
    )

    # -----------------------------------------------------
    # TOTAL USAGE LOGS
    # -----------------------------------------------------
    total_logs = len(usage_logs)

    # -----------------------------------------------------
    # UNIQUE ACTIVE DAYS
    # -----------------------------------------------------
    unique_days = len(
        set(
            log.usage_date
            for log in usage_logs
        )
    )

    # -----------------------------------------------------
    # AVERAGE HOURS PER USAGE DAY
    # -----------------------------------------------------
    average_hours = (
        total_hours / unique_days
        if unique_days > 0
        else 0
    )

    # -----------------------------------------------------
    # USAGE BY SUBSCRIPTION
    # -----------------------------------------------------
    subscription_usage = {}

    for log in usage_logs:

        if log.subscription:

            name = log.subscription.name

            subscription_usage[name] = (
                subscription_usage.get(name, 0)
                + float(log.hours_used or 0)
            )

    usage_labels = list(
        subscription_usage.keys()
    )

    usage_values = list(
        subscription_usage.values()
    )

    return render_template(
        'analytics/usage_analysis.html',
        usage_logs=usage_logs,
        total_hours=round(total_hours, 2),
        total_logs=total_logs,
        unique_days=unique_days,
        average_hours=round(average_hours, 2),
        usage_labels=usage_labels,
        usage_values=usage_values
    )


# =========================================================
# VALUE SCORE
# =========================================================
@analytics_bp.route('/value-score')
@login_required
def value_score():

    # Get complete value score information
    data = analytics.get_value_scores(
        current_user.id
    )

    # -----------------------------------------------------
    # SUMMARY CALCULATIONS
    # -----------------------------------------------------
    if data:

        # Average score of all active subscriptions
        average_score = (
            sum(
                item['value_score']
                for item in data
            )
            / len(data)
        )

        # High value = score 60 or above
        high_value_count = sum(
            1
            for item in data
            if item['value_score'] >= 60
        )

        # Low value = score below 40
        low_value_count = sum(
            1
            for item in data
            if item['value_score'] < 40
        )

    else:

        average_score = 0
        high_value_count = 0
        low_value_count = 0

    return render_template(
        'analytics/value_score.html',
        data=data,
        average_score=round(
            average_score,
            2
        ),
        high_value_count=high_value_count,
        low_value_count=low_value_count
    )