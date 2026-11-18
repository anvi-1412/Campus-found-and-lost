from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import ItemModel, ClaimModel
from database import log_activity
from routes import login_required, save_uploaded_file

claims_bp = Blueprint('claims', __name__)

@claims_bp.route('/claim/<int:item_id>', methods=['GET', 'POST'])
@login_required
def submit_claim(item_id):
    item = ItemModel.get_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('items.browse'))

    current_user_id = session['user_id']

    # Guard: Prevent students from claiming their own found items
    if item['user_id'] == current_user_id:
        flash('You cannot claim an item that you reported.', 'warning')
        return redirect(url_for('items.details', item_id=item_id))

    # Guard: Cannot claim items that are already returned or closed
    if item['status'] in ('Returned', 'Closed'):
        flash(f'This item is already marked as {item["status"]} and cannot be claimed.', 'warning')
        return redirect(url_for('items.details', item_id=item_id))

    # Guard: Check for duplicate pending claim
    if ClaimModel.has_pending_claim(item_id, current_user_id):
        flash('You already have an active pending claim for this item. Please wait for administrator review.', 'info')
        return redirect(url_for('items.details', item_id=item_id))

    if request.method == 'POST':
        proof_description = request.form.get('proof_description', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        errors = []
        if not proof_description or len(proof_description) < 15:
            errors.append('Please provide detailed proof of ownership (minimum 15 characters, e.g. serial numbers, identifying marks, screen wallpaper, contents).')
        if not contact_phone:
            errors.append('Please provide a contact phone number for verification.')

        proof_image_file = request.files.get('proof_image')
        proof_image = None
        if proof_image_file and proof_image_file.filename:
            proof_image = save_uploaded_file(proof_image_file)
            if not proof_image:
                errors.append('Uploaded proof image must be JPG, PNG, WEBP, or GIF.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('claim_item.html', item=item, form_data=request.form)

        claim_id = ClaimModel.create(
            item_id=item_id,
            claimer_id=current_user_id,
            proof_description=proof_description,
            proof_image=proof_image,
            contact_phone=contact_phone
        )

        log_activity(current_user_id, 'SUBMIT_CLAIM', f"Submitted claim #{claim_id} for item #{item_id} ({item['title']})")
        flash('Claim submitted successfully! Campus Safety & Security will review your verification details.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('claim_item.html', item=item, form_data={})


@claims_bp.route('/my-claims')
@login_required
def my_claims():
    current_user_id = session['user_id']
    claims = ClaimModel.get_by_user(current_user_id)
    return render_template('profile.html', active_tab='claims', claims=claims)
