from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.database.models import db, Subscription


subscriptions_bp = Blueprint(
    'subscriptions',
    __name__,
    url_prefix='/subscriptions'
)


# =========================================================
# SUBSCRIPTION LIST
# =========================================================
@subscriptions_bp.route('/')
@login_required
def list_subscriptions():

    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subscription.name
    ).all()

    return render_template(
        'subscriptions/list.html',
        subscriptions=subscriptions
    )


# =========================================================
# ADD SUBSCRIPTION
# =========================================================
@subscriptions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_subscription():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        monthly_cost = request.form.get('monthly_cost', '').strip()
        annual_cost = request.form.get('annual_cost', '').strip()
        billing_cycle = request.form.get(
            'billing_cycle',
            'Monthly'
        ).strip()
        start_date = request.form.get('start_date', '').strip()
        renewal_date = request.form.get(
            'renewal_date',
            ''
        ).strip()
        notes = request.form.get('notes', '').strip()

        # -------------------------
        # Required fields
        # -------------------------
        if not name:
            flash('Subscription name is required.', 'danger')
            return redirect(url_for('subscriptions.add_subscription'))

        if not category:
            flash('Please select a category.', 'danger')
            return redirect(url_for('subscriptions.add_subscription'))

        if not monthly_cost:
            flash('Monthly cost is required.', 'danger')
            return redirect(url_for('subscriptions.add_subscription'))

        if not start_date:
            flash('Start date is required.', 'danger')
            return redirect(url_for('subscriptions.add_subscription'))

        # -------------------------
        # Convert monthly cost
        # -------------------------
        try:
            monthly_cost = float(monthly_cost)

            if monthly_cost < 0:
                raise ValueError

        except ValueError:
            flash(
                'Monthly cost must be a valid positive number.',
                'danger'
            )
            return redirect(
                url_for('subscriptions.add_subscription')
            )

        # -------------------------
        # Convert annual cost
        # -------------------------
        if annual_cost:

            try:
                annual_cost = float(annual_cost)

                if annual_cost < 0:
                    raise ValueError

            except ValueError:
                flash(
                    'Annual cost must be a valid positive number.',
                    'danger'
                )
                return redirect(
                    url_for('subscriptions.add_subscription')
                )

        else:
            annual_cost = None

        # -------------------------
        # Convert dates
        # -------------------------
        try:

            start_date = datetime.strptime(
                start_date,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            flash(
                'Invalid start date.',
                'danger'
            )

            return redirect(
                url_for('subscriptions.add_subscription')
            )

        if renewal_date:

            try:

                renewal_date = datetime.strptime(
                    renewal_date,
                    '%Y-%m-%d'
                ).date()

            except ValueError:

                flash(
                    'Invalid renewal date.',
                    'danger'
                )

                return redirect(
                    url_for('subscriptions.add_subscription')
                )

        else:
            renewal_date = None

        # -------------------------
        # Create subscription
        # -------------------------
        subscription = Subscription(
            user_id=current_user.id,
            name=name,
            category=category,
            monthly_cost=monthly_cost,
            annual_cost=annual_cost,
            billing_cycle=billing_cycle,
            start_date=start_date,
            renewal_date=renewal_date,
            status='Active',
            notes=notes
        )

        db.session.add(subscription)
        db.session.commit()

        flash(
            'Subscription added successfully!',
            'success'
        )

        return redirect(
            url_for('subscriptions.list_subscriptions')
        )

    return render_template(
        'subscriptions/add.html'
    )


# =========================================================
# EDIT SUBSCRIPTION
# =========================================================
@subscriptions_bp.route('/edit/<int:subscription_id>', methods=['GET', 'POST'])
@login_required
def edit_subscription(subscription_id):

    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first()

    if not subscription:

        flash(
            'Subscription not found.',
            'danger'
        )

        return redirect(
            url_for('subscriptions.list_subscriptions')
        )

    if request.method == 'POST':

        name = request.form.get(
            'name',
            ''
        ).strip()

        category = request.form.get(
            'category',
            ''
        ).strip()

        monthly_cost = request.form.get(
            'monthly_cost',
            ''
        ).strip()

        annual_cost = request.form.get(
            'annual_cost',
            ''
        ).strip()

        billing_cycle = request.form.get(
            'billing_cycle',
            'Monthly'
        ).strip()

        start_date = request.form.get(
            'start_date',
            ''
        ).strip()

        renewal_date = request.form.get(
            'renewal_date',
            ''
        ).strip()

        status = request.form.get(
            'status',
            'Active'
        ).strip()

        notes = request.form.get(
            'notes',
            ''
        ).strip()

        # -------------------------
        # Required fields
        # -------------------------
        if not name:
            flash(
                'Subscription name is required.',
                'danger'
            )
            return redirect(
                url_for(
                    'subscriptions.edit_subscription',
                    subscription_id=subscription_id
                )
            )

        if not category:
            flash(
                'Category is required.',
                'danger'
            )
            return redirect(
                url_for(
                    'subscriptions.edit_subscription',
                    subscription_id=subscription_id
                )
            )

        # -------------------------
        # Monthly cost
        # -------------------------
        try:

            monthly_cost = float(monthly_cost)

            if monthly_cost < 0:
                raise ValueError

        except ValueError:

            flash(
                'Monthly cost must be a valid positive number.',
                'danger'
            )

            return redirect(
                url_for(
                    'subscriptions.edit_subscription',
                    subscription_id=subscription_id
                )
            )

        # -------------------------
        # Annual cost
        # -------------------------
        if annual_cost:

            try:

                annual_cost = float(annual_cost)

                if annual_cost < 0:
                    raise ValueError

            except ValueError:

                flash(
                    'Annual cost must be a valid positive number.',
                    'danger'
                )

                return redirect(
                    url_for(
                        'subscriptions.edit_subscription',
                        subscription_id=subscription_id
                    )
                )

        else:
            annual_cost = None

        # -------------------------
        # Dates
        # -------------------------
        if start_date:

            try:

                start_date = datetime.strptime(
                    start_date,
                    '%Y-%m-%d'
                ).date()

            except ValueError:

                flash(
                    'Invalid start date.',
                    'danger'
                )

                return redirect(
                    url_for(
                        'subscriptions.edit_subscription',
                        subscription_id=subscription_id
                    )
                )

        else:

            flash(
                'Start date is required.',
                'danger'
            )

            return redirect(
                url_for(
                    'subscriptions.edit_subscription',
                    subscription_id=subscription_id
                )
            )

        if renewal_date:

            try:

                renewal_date = datetime.strptime(
                    renewal_date,
                    '%Y-%m-%d'
                ).date()

            except ValueError:

                flash(
                    'Invalid renewal date.',
                    'danger'
                )

                return redirect(
                    url_for(
                        'subscriptions.edit_subscription',
                        subscription_id=subscription_id
                    )
                )

        else:
            renewal_date = None

        # -------------------------
        # Update subscription
        # -------------------------
        subscription.name = name
        subscription.category = category
        subscription.monthly_cost = monthly_cost
        subscription.annual_cost = annual_cost
        subscription.billing_cycle = billing_cycle
        subscription.start_date = start_date
        subscription.renewal_date = renewal_date
        subscription.status = status
        subscription.notes = notes

        db.session.commit()

        flash(
            'Subscription updated successfully!',
            'success'
        )

        return redirect(
            url_for('subscriptions.list_subscriptions')
        )

    return render_template(
        'subscriptions/edit.html',
        subscription=subscription
    )


# =========================================================
# DELETE SUBSCRIPTION
# =========================================================
@subscriptions_bp.route(
    '/delete/<int:subscription_id>',
    methods=['POST']
)
@login_required
def delete_subscription(subscription_id):

    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first()

    if not subscription:

        flash(
            'Subscription not found.',
            'danger'
        )

        return redirect(
            url_for('subscriptions.list_subscriptions')
        )

    db.session.delete(subscription)
    db.session.commit()

    flash(
        'Subscription deleted successfully.',
        'success'
    )

    return redirect(
        url_for('subscriptions.list_subscriptions')
    )