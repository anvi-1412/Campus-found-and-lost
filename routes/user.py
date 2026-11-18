from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import UserModel, ItemModel, ClaimModel, StatsModel
from database import log_activity
from routes import login_required
from werkzeug.security import check_password_hash
from config import Config

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id)
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    user_stats = StatsModel.get_user_stats(user_id)
    system_stats = StatsModel.get_system_stats()

    my_lost_items = ItemModel.get_by_user(user_id, item_type='lost')
    my_found_items = ItemModel.get_by_user(user_id, item_type='found')
    my_claims = ClaimModel.get_by_user(user_id)

    # Recent campus items for quick glance
    recent_items = ItemModel.get_recent(limit=4)

    return render_template(
        'dashboard.html',
        user=user,
        stats=user_stats,
        system_stats=system_stats,
        lost_items=my_lost_items,
        found_items=my_found_items,
        claims=my_claims,
        recent_items=recent_items
    )


@user_bp.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    my_lost = ItemModel.get_by_user(user_id, item_type='lost')
    my_found = ItemModel.get_by_user(user_id, item_type='found')
    my_claims = ClaimModel.get_by_user(user_id)
    user_stats = StatsModel.get_user_stats(user_id)

    active_tab = request.args.get('tab', 'overview')

    return render_template(
        'profile.html',
        user=user,
        lost_items=my_lost,
        found_items=my_found,
        claims=my_claims,
        stats=user_stats,
        departments=Config.DEPARTMENTS,
        active_tab=active_tab
    )


@user_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name:
        flash('Full Name is required.', 'danger')
        return redirect(url_for('user.profile', tab='edit'))

    if not department:
        flash('Department is required.', 'danger')
        return redirect(url_for('user.profile', tab='edit'))

    UserModel.update_profile(user_id, name, department, phone)
    session['user_name'] = name
    session['department'] = department

    log_activity(user_id, 'PROFILE_UPDATE', f"User {name} updated their profile.")
    flash('Profile details updated successfully.', 'success')
    return redirect(url_for('user.profile', tab='overview'))


@user_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    user = UserModel.get_by_id(user_id)
    if not user or not check_password_hash(user['password_hash'], current_password):
        flash('Current password entered is incorrect.', 'danger')
        return redirect(url_for('user.profile', tab='security'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('user.profile', tab='security'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('user.profile', tab='security'))

    UserModel.update_password(user_id, new_password)
    log_activity(user_id, 'PASSWORD_CHANGE', "User changed their password.")
    flash('Password changed successfully.', 'success')
    return redirect(url_for('user.profile', tab='overview'))
