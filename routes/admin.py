from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import UserModel, ItemModel, ClaimModel, StatsModel
from database import log_activity, query_db
from routes import admin_required
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = StatsModel.get_system_stats()
    
    # Claims
    claims_filter = request.args.get('claims_status', 'All')
    claims = ClaimModel.get_all(status=claims_filter if claims_filter != 'All' else None)

    # Items
    item_type = request.args.get('item_type', 'all')
    category = request.args.get('category', 'All')
    status = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()
    
    items = ItemModel.get_all(
        item_type=item_type if item_type != 'all' else None,
        category=category,
        status=status,
        search=search if search else None
    )

    # Users
    users = UserModel.get_all()

    # Activity logs
    logs = query_db("""
        SELECT l.*, u.name as user_name, u.email as user_email, u.role as user_role 
        FROM activity_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 25
    """)

    active_tab = request.args.get('tab', 'overview')

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        claims=claims,
        claims_filter=claims_filter,
        items=items,
        users=users,
        logs=logs,
        categories=Config.CATEGORIES,
        statuses=Config.ITEM_STATUSES,
        active_tab=active_tab,
        selected_type=item_type,
        selected_category=category,
        selected_status=status,
        search_query=search
    )


@admin_bp.route('/claims/<int:claim_id>/action', methods=['POST'])
@admin_required
def claim_action(claim_id):
    action = request.form.get('action') # 'approve' or 'reject'
    admin_remarks = request.form.get('admin_remarks', '').strip()
    admin_id = session.get('user_id')

    if action not in ('approve', 'reject'):
        flash('Invalid claim action requested.', 'danger')
        return redirect(url_for('admin.dashboard', tab='claims'))

    status = 'Approved' if action == 'approve' else 'Rejected'
    success = ClaimModel.update_status(claim_id, status, admin_remarks)

    if success:
        log_activity(admin_id, f"CLAIM_{status.upper()}", f"Admin marked claim #{claim_id} as {status}. Remarks: {admin_remarks}")
        flash(f'Claim #{claim_id} successfully marked as {status}.', 'success')
    else:
        flash('Could not find or update the specified claim.', 'danger')

    return redirect(url_for('admin.dashboard', tab='claims'))


@admin_bp.route('/items/<int:item_id>/status', methods=['POST'])
@admin_required
def item_status(item_id):
    new_status = request.form.get('status')
    admin_id = session.get('user_id')

    if new_status in Config.ITEM_STATUSES:
        ItemModel.update_status(item_id, new_status)
        log_activity(admin_id, 'ADMIN_UPDATE_ITEM_STATUS', f"Admin set status of item #{item_id} to {new_status}")
        flash(f'Item #{item_id} status updated to "{new_status}".', 'success')
    else:
        flash('Invalid status provided.', 'danger')

    return redirect(url_for('admin.dashboard', tab='items'))


@admin_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@admin_required
def item_delete(item_id):
    item = ItemModel.get_by_id(item_id)
    admin_id = session.get('user_id')

    if item:
        ItemModel.delete(item_id)
        log_activity(admin_id, 'ADMIN_DELETE_ITEM', f"Admin deleted item #{item_id} ({item['title']})")
        flash(f'Item #{item_id} deleted permanently.', 'info')
    else:
        flash('Item not found.', 'danger')

    return redirect(url_for('admin.dashboard', tab='items'))


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@admin_required
def user_role(user_id):
    admin_id = session.get('user_id')
    new_role = request.form.get('role')

    if user_id == admin_id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.dashboard', tab='users'))

    if new_role in ('student', 'admin'):
        UserModel.set_role(user_id, new_role)
        log_activity(admin_id, 'ADMIN_CHANGE_USER_ROLE', f"User #{user_id} role changed to {new_role}")
        flash(f'User role updated to "{new_role}".', 'success')
    else:
        flash('Invalid role specified.', 'danger')

    return redirect(url_for('admin.dashboard', tab='users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    admin_id = session.get('user_id')

    if user_id == admin_id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.dashboard', tab='users'))

    target_user = UserModel.get_by_id(user_id)
    if target_user:
        UserModel.delete(user_id)
        log_activity(admin_id, 'ADMIN_DELETE_USER', f"Admin deleted user #{user_id} ({target_user['name']})")
        flash(f"User {target_user['name']} has been removed.", 'info')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin.dashboard', tab='users'))
