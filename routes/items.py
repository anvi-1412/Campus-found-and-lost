from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models import ItemModel, ClaimModel, UserModel
from database import log_activity
from routes import login_required, save_uploaded_file
from config import Config
from datetime import date

items_bp = Blueprint('items', __name__)

@items_bp.route('/browse')
@items_bp.route('/items')
def browse():
    item_type = request.args.get('type', 'all')
    category = request.args.get('category', 'All')
    location = request.args.get('location', 'All')
    status = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()

    items = ItemModel.get_all(
        item_type=item_type if item_type != 'all' else None,
        category=category,
        location=location,
        status=status,
        search=search if search else None
    )

    return render_template(
        'browse_items.html',
        items=items,
        selected_type=item_type,
        selected_category=category,
        selected_location=location,
        selected_status=status,
        search_query=search,
        categories=Config.CATEGORIES,
        locations=Config.LOCATIONS,
        statuses=Config.ITEM_STATUSES
    )


@items_bp.route('/items/<int:item_id>')
def details(item_id):
    item = ItemModel.get_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('items.browse'))

    current_user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Check if current user already has a pending claim on this item
    has_claimed = False
    if current_user_id:
        has_claimed = ClaimModel.has_pending_claim(item_id, current_user_id)

    # Claims list if user is the reporter or admin
    claims = []
    if current_user_id and (current_user_id == item['user_id'] or user_role == 'admin'):
        claims = ClaimModel.get_by_item(item_id)

    return render_template(
        'item_details.html',
        item=item,
        has_claimed=has_claimed,
        claims=claims,
        is_owner=(current_user_id == item['user_id']),
        is_admin=(user_role == 'admin')
    )


@items_bp.route('/report/lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        event_date = request.form.get('event_date', '').strip()
        contact_info = request.form.get('contact_info', '').strip()

        # Validation
        errors = []
        if not title:
            errors.append('Item name/title is required.')
        if not category:
            errors.append('Please select an item category.')
        if not description or len(description) < 10:
            errors.append('Please provide a descriptive explanation (minimum 10 characters).')
        if not location:
            errors.append('Please specify where the item was last seen.')
        if not event_date:
            errors.append('Please select the date the item was lost.')

        image_file = request.files.get('image')
        image_path = None
        if image_file and image_file.filename:
            image_path = save_uploaded_file(image_file)
            if not image_path:
                errors.append('Uploaded file is not a supported image format (allowed: JPG, PNG, WEBP, GIF).')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'report_lost.html',
                categories=Config.CATEGORIES,
                locations=Config.LOCATIONS,
                today=date.today().isoformat(),
                form_data=request.form
            )

        user_id = session['user_id']
        contact_to_save = contact_info if contact_info else f"{session.get('user_name')} ({session.get('user_email')})"

        item_id = ItemModel.create(
            user_id=user_id,
            item_type='lost',
            title=title,
            category=category,
            description=description,
            location=location,
            event_date=event_date,
            image_path=image_path,
            status='Lost',
            custody_info=None,
            contact_info=contact_to_save
        )

        log_activity(user_id, 'REPORT_LOST', f"Reported lost item #{item_id}: {title}")
        flash('Your lost item report has been published successfully. We hope it is recovered soon!', 'success')
        return redirect(url_for('items.details', item_id=item_id))

    return render_template(
        'report_lost.html',
        categories=Config.CATEGORIES,
        locations=Config.LOCATIONS,
        today=date.today().isoformat(),
        form_data={}
    )


@items_bp.route('/report/found', methods=['GET', 'POST'])
@login_required
def report_found():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        event_date = request.form.get('event_date', '').strip()
        custody_info = request.form.get('custody_info', '').strip()
        contact_info = request.form.get('contact_info', '').strip()

        errors = []
        if not title:
            errors.append('Item name/title is required.')
        if not category:
            errors.append('Please select an item category.')
        if not description or len(description) < 10:
            errors.append('Please provide a description (minimum 10 characters).')
        if not location:
            errors.append('Please specify where the item was found.')
        if not event_date:
            errors.append('Please select the date found.')
        if not custody_info:
            errors.append('Please state where the item is currently kept (e.g., Security Desk, Library Front Desk).')

        image_file = request.files.get('image')
        image_path = None
        if image_file and image_file.filename:
            image_path = save_uploaded_file(image_file)
            if not image_path:
                errors.append('Uploaded file is not a supported image format (allowed: JPG, PNG, WEBP, GIF).')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'report_found.html',
                categories=Config.CATEGORIES,
                locations=Config.LOCATIONS,
                today=date.today().isoformat(),
                form_data=request.form
            )

        user_id = session['user_id']
        contact_to_save = contact_info if contact_info else f"{session.get('user_name')} ({session.get('user_email')})"

        item_id = ItemModel.create(
            user_id=user_id,
            item_type='found',
            title=title,
            category=category,
            description=description,
            location=location,
            event_date=event_date,
            image_path=image_path,
            status='Found',
            custody_info=custody_info,
            contact_info=contact_to_save
        )

        log_activity(user_id, 'REPORT_FOUND', f"Reported found item #{item_id}: {title}")
        flash('Thank you for your honesty! The found item report has been posted.', 'success')
        return redirect(url_for('items.details', item_id=item_id))

    return render_template(
        'report_found.html',
        categories=Config.CATEGORIES,
        locations=Config.LOCATIONS,
        today=date.today().isoformat(),
        form_data={}
    )


@items_bp.route('/items/<int:item_id>/status', methods=['POST'])
@login_required
def update_status(item_id):
    item = ItemModel.get_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('items.browse'))

    current_user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Allow reporter or admin to update status
    if item['user_id'] != current_user_id and user_role != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('items.details', item_id=item_id))

    new_status = request.form.get('status')
    if new_status in Config.ITEM_STATUSES:
        ItemModel.update_status(item_id, new_status)
        log_activity(current_user_id, 'UPDATE_ITEM_STATUS', f"Item #{item_id} status updated to {new_status}")
        flash(f'Status updated to "{new_status}".', 'success')
    else:
        flash('Invalid status provided.', 'danger')

    return redirect(url_for('items.details', item_id=item_id))


@items_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete(item_id):
    item = ItemModel.get_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('items.browse'))

    current_user_id = session.get('user_id')
    user_role = session.get('user_role')

    if item['user_id'] != current_user_id and user_role != 'admin':
        flash('Unauthorized to delete this item.', 'danger')
        return redirect(url_for('items.details', item_id=item_id))

    ItemModel.delete(item_id)
    log_activity(current_user_id, 'DELETE_ITEM', f"Deleted item #{item_id} ({item['title']})")
    flash('Item listing deleted successfully.', 'info')

    if user_role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('user.dashboard'))
