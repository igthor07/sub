from datetime import datetime, timedelta

from app.database.models import Subscription, UsageLog


class AnalyticsEngine:

    # =========================================================
    # TOTAL MONTHLY SPENDING
    # =========================================================
    def calculate_total_spending(self, user_id, months=12):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).all()

        total = sum(
            float(subscription.monthly_cost or 0)
            for subscription in subscriptions
        )

        return total

    # =========================================================
    # COST BREAKDOWN
    # =========================================================
    def get_cost_breakdown(self, user_id):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).order_by(
            Subscription.monthly_cost.desc()
        ).all()

        breakdown = []

        for subscription in subscriptions:

            monthly_cost = float(
                subscription.monthly_cost or 0
            )

            annual_cost = (
                float(subscription.annual_cost)
                if subscription.annual_cost is not None
                else monthly_cost * 12
            )

            breakdown.append({
                'id': subscription.id,
                'name': subscription.name,
                'category': subscription.category,
                'monthly_cost': monthly_cost,
                'annual_cost': annual_cost,
                'billing_cycle': subscription.billing_cycle
            })

        return breakdown

    # =========================================================
    # COST PER USE
    # =========================================================
    def calculate_cost_per_use(self, subscription_id, user_id=None):

        query = Subscription.query.filter_by(
            id=subscription_id
        )

        if user_id is not None:
            query = query.filter_by(
                user_id=user_id
            )

        subscription = query.first()

        if not subscription:
            return 0

        usage_logs_query = UsageLog.query.filter_by(
            subscription_id=subscription_id
        )

        if user_id is not None:
            usage_logs_query = usage_logs_query.filter_by(
                user_id=user_id
            )

        usage_logs = usage_logs_query.all()

        total_hours = sum(
            float(log.hours_used or 0)
            for log in usage_logs
        )

        if total_hours <= 0:
            return 0

        return float(
            subscription.monthly_cost or 0
        ) / total_hours

    # =========================================================
    # AVERAGE COST PER USE
    # =========================================================
    def calculate_average_cost_per_use(self, user_id):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).all()

        if not subscriptions:
            return 0

        total_cost = 0
        total_hours = 0

        for subscription in subscriptions:

            total_cost += float(
                subscription.monthly_cost or 0
            )

            usage_logs = UsageLog.query.filter_by(
                user_id=user_id,
                subscription_id=subscription.id
            ).all()

            total_hours += sum(
                float(log.hours_used or 0)
                for log in usage_logs
            )

        if total_hours <= 0:
            return 0

        return total_cost / total_hours

    # =========================================================
    # VALUE SCORE
    # =========================================================
    def calculate_value_score(self, subscription_id, user_id=None):

        query = Subscription.query.filter_by(
            id=subscription_id
        )

        if user_id is not None:
            query = query.filter_by(
                user_id=user_id
            )

        subscription = query.first()

        if not subscription:
            return 0

        # Last 30 days
        thirty_days_ago = (
            datetime.utcnow().date()
            - timedelta(days=30)
        )

        usage_logs_query = UsageLog.query.filter(
            UsageLog.subscription_id == subscription_id,
            UsageLog.usage_date >= thirty_days_ago
        )

        if user_id is not None:
            usage_logs_query = usage_logs_query.filter(
                UsageLog.user_id == user_id
            )

        usage_logs = usage_logs_query.all()

        # -----------------------------------------------------
        # TOTAL HOURS
        # -----------------------------------------------------
        total_hours = sum(
            float(log.hours_used or 0)
            for log in usage_logs
        )

        # -----------------------------------------------------
        # UNIQUE USAGE DAYS
        # -----------------------------------------------------
        usage_days = len(
            set(
                log.usage_date
                for log in usage_logs
            )
        )

        # -----------------------------------------------------
        # FREQUENCY SCORE
        # 60% WEIGHT
        # -----------------------------------------------------
        frequency_score = min(
            (usage_days / 30) * 100,
            100
        )

        # -----------------------------------------------------
        # COST EFFICIENCY SCORE
        # 40% WEIGHT
        # -----------------------------------------------------
        monthly_cost = float(
            subscription.monthly_cost or 0
        )

        if total_hours > 0 and monthly_cost > 0:

            cost_per_hour = (
                monthly_cost / total_hours
            )

            if cost_per_hour <= 1:
                efficiency_score = 100

            elif cost_per_hour <= 3:
                efficiency_score = 80

            elif cost_per_hour <= 5:
                efficiency_score = 60

            elif cost_per_hour <= 10:
                efficiency_score = 40

            else:
                efficiency_score = 20

        elif total_hours > 0:

            efficiency_score = 100

        else:

            efficiency_score = 0

        # -----------------------------------------------------
        # FINAL VALUE SCORE
        # -----------------------------------------------------
        value_score = (
            frequency_score * 0.6
            + efficiency_score * 0.4
        )

        return round(
            min(value_score, 100),
            2
        )

    # =========================================================
    # LOW UTILIZATION SUBSCRIPTIONS
    # =========================================================
    def get_low_utilization_subscriptions(self, user_id):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).all()

        low_utilization = []

        for subscription in subscriptions:

            score = self.calculate_value_score(
                subscription.id,
                user_id
            )

            if score < 50:

                low_utilization.append({
                    'id': subscription.id,
                    'name': subscription.name,
                    'monthly_cost': float(
                        subscription.monthly_cost or 0
                    ),
                    'score': score
                })

        return low_utilization

    # =========================================================
    # USAGE PATTERN
    # =========================================================
    def get_usage_pattern(self, user_id):

        usage_logs = UsageLog.query.filter_by(
            user_id=user_id
        ).order_by(
            UsageLog.usage_date
        ).all()

        pattern = {}

        for log in usage_logs:

            date_string = log.usage_date.strftime(
                '%Y-%m-%d'
            )

            pattern[date_string] = (
                pattern.get(date_string, 0)
                + float(log.hours_used or 0)
            )

        return pattern

    # =========================================================
    # DASHBOARD CHART DATA
    # =========================================================
    def get_dashboard_chart_data(self, user_id):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).order_by(
            Subscription.name
        ).all()

        subscription_names = [
            subscription.name
            for subscription in subscriptions
        ]

        subscription_costs = [
            float(subscription.monthly_cost or 0)
            for subscription in subscriptions
        ]

        # Last 30 days
        thirty_days_ago = (
            datetime.utcnow().date()
            - timedelta(days=30)
        )

        usage_logs = UsageLog.query.filter(
            UsageLog.user_id == user_id,
            UsageLog.usage_date >= thirty_days_ago
        ).order_by(
            UsageLog.usage_date
        ).all()

        usage_by_date = {}

        for log in usage_logs:

            date_string = log.usage_date.strftime(
                '%Y-%m-%d'
            )

            usage_by_date[date_string] = (
                usage_by_date.get(date_string, 0)
                + float(log.hours_used or 0)
            )

        usage_dates = list(
            usage_by_date.keys()
        )

        usage_hours = list(
            usage_by_date.values()
        )

        return {
            'subscription_names': subscription_names,
            'subscription_costs': subscription_costs,
            'usage_dates': usage_dates,
            'usage_hours': usage_hours
        }

    # =========================================================
    # COMPLETE VALUE SCORE DATA
    # =========================================================
    def get_value_scores(self, user_id):

        subscriptions = Subscription.query.filter_by(
            user_id=user_id,
            status='Active'
        ).all()

        data = []

        # Last 30 days
        thirty_days_ago = (
            datetime.utcnow().date()
            - timedelta(days=30)
        )

        for subscription in subscriptions:

            # -------------------------------------------------
            # GET USAGE LOGS
            # -------------------------------------------------
            usage_logs = UsageLog.query.filter(
                UsageLog.user_id == user_id,
                UsageLog.subscription_id == subscription.id,
                UsageLog.usage_date >= thirty_days_ago
            ).all()

            # -------------------------------------------------
            # TOTAL USAGE HOURS
            # -------------------------------------------------
            usage_hours = sum(
                float(log.hours_used or 0)
                for log in usage_logs
            )

            # -------------------------------------------------
            # VALUE SCORE
            # -------------------------------------------------
            score = self.calculate_value_score(
                subscription.id,
                user_id
            )

            # -------------------------------------------------
            # MONTHLY COST
            # -------------------------------------------------
            monthly_cost = float(
                subscription.monthly_cost or 0
            )

            # -------------------------------------------------
            # COST PER HOUR
            # -------------------------------------------------
            if usage_hours > 0:

                cost_per_use = (
                    monthly_cost / usage_hours
                )

            else:

                cost_per_use = 0

            # -------------------------------------------------
            # RECOMMENDATION
            # -------------------------------------------------
            if score >= 75:

                recommendation = 'Keep'

            elif score >= 50:

                recommendation = 'Review'

            else:

                recommendation = 'Consider Cancelling'

            # -------------------------------------------------
            # FINAL DATA
            # -------------------------------------------------
            data.append({
                'id': subscription.id,
                'name': subscription.name,
                'category': subscription.category,
                'monthly_cost': monthly_cost,
                'usage_hours': usage_hours,
                'cost_per_use': cost_per_use,
                'value_score': score,
                'recommendation': recommendation
            })

        # Highest score first
        return sorted(
            data,
            key=lambda x: x['value_score'],
            reverse=True
        )