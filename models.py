from database import query_db, execute_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class UserModel:
    @staticmethod
    def get_by_id(user_id):
        return query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)

    @staticmethod
    def get_by_email(email):
        return query_db("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),), one=True)

    @staticmethod
    def get_by_student_id(student_id):
        return query_db("SELECT * FROM users WHERE UPPER(student_id) = UPPER(?)", (student_id.strip(),), one=True)

    @staticmethod
    def create(name, email, student_id, department, phone, password, role='student'):
        password_hash = generate_password_hash(password)
        user_id = execute_db("""
            INSERT INTO users (name, email, student_id, department, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), email.strip().lower(), student_id.strip().upper(), department.strip(), phone.strip() if phone else None, password_hash, role))
        return user_id

    @staticmethod
    def update_profile(user_id, name, department, phone):
        execute_db("""
            UPDATE users SET name = ?, department = ?, phone = ? WHERE id = ?
        """, (name.strip(), department.strip(), phone.strip() if phone else None, user_id))

    @staticmethod
    def update_password(user_id, new_password):
        password_hash = generate_password_hash(new_password)
        execute_db("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))

    @staticmethod
    def get_all():
        return query_db("SELECT id, name, email, student_id, department, phone, role, created_at FROM users ORDER BY created_at DESC")

    @staticmethod
    def set_role(user_id, role):
        execute_db("UPDATE users SET role = ? WHERE id = ?", (role, user_id))

    @staticmethod
    def delete(user_id):
        execute_db("DELETE FROM users WHERE id = ?", (user_id,))


class ItemModel:
    @staticmethod
    def get_by_id(item_id):
        return query_db("""
            SELECT i.*, u.name as reporter_name, u.email as reporter_email, 
                   u.student_id as reporter_student_id, u.department as reporter_dept
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.id = ?
        """, (item_id,), one=True)

    @staticmethod
    def get_all(item_type=None, category=None, location=None, status=None, search=None, limit=None, offset=None):
        sql = """
            SELECT i.*, u.name as reporter_name, u.department as reporter_dept
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE 1=1
        """
        params = []

        if item_type and item_type.lower() in ('lost', 'found'):
            sql += " AND i.item_type = ?"
            params.append(item_type.lower())

        if category and category != 'All':
            sql += " AND i.category = ?"
            params.append(category)

        if location and location != 'All':
            sql += " AND i.location = ?"
            params.append(location)

        if status and status != 'All':
            sql += " AND i.status = ?"
            params.append(status)

        if search:
            sql += " AND (i.title LIKE ? OR i.description LIKE ? OR i.location LIKE ? OR i.category LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term])

        sql += " ORDER BY i.created_at DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(int(limit))
            if offset:
                sql += " OFFSET ?"
                params.append(int(offset))

        return query_db(sql, params)

    @staticmethod
    def get_by_user(user_id, item_type=None):
        if item_type:
            return query_db("""
                SELECT * FROM items 
                WHERE user_id = ? AND item_type = ? 
                ORDER BY created_at DESC
            """, (user_id, item_type.lower()))
        return query_db("""
            SELECT * FROM items 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))

    @staticmethod
    def create(user_id, item_type, title, category, description, location, event_date, image_path, status, custody_info=None, contact_info=None):
        item_id = execute_db("""
            INSERT INTO items (
                user_id, item_type, title, category, description,
                location, event_date, image_path, status, custody_info, contact_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, item_type.lower(), title.strip(), category, description.strip(),
            location, event_date, image_path, status, custody_info.strip() if custody_info else None, contact_info.strip() if contact_info else None
        ))
        return item_id

    @staticmethod
    def update(item_id, title, category, description, location, event_date, image_path=None, status=None, custody_info=None, contact_info=None):
        if image_path:
            execute_db("""
                UPDATE items SET 
                    title = ?, category = ?, description = ?, location = ?, 
                    event_date = ?, image_path = ?, custody_info = ?, contact_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title.strip(), category, description.strip(), location, event_date, image_path, custody_info, contact_info, item_id))
        else:
            execute_db("""
                UPDATE items SET 
                    title = ?, category = ?, description = ?, location = ?, 
                    event_date = ?, custody_info = ?, contact_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title.strip(), category, description.strip(), location, event_date, custody_info, contact_info, item_id))

        if status:
            execute_db("UPDATE items SET status = ? WHERE id = ?", (status, item_id))

    @staticmethod
    def update_status(item_id, status):
        execute_db("""
            UPDATE items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (status, item_id))

    @staticmethod
    def delete(item_id):
        execute_db("DELETE FROM items WHERE id = ?", (item_id,))

    @staticmethod
    def get_recent(limit=6):
        return query_db("""
            SELECT i.*, u.name as reporter_name 
            FROM items i 
            JOIN users u ON i.user_id = u.id 
            ORDER BY i.created_at DESC 
            LIMIT ?
        """, (limit,))


class ClaimModel:
    @staticmethod
    def get_by_id(claim_id):
        return query_db("""
            SELECT c.*, 
                   i.title as item_title, i.item_type, i.status as item_status, i.location as item_location, i.category as item_category, i.image_path as item_image,
                   u.name as claimer_name, u.email as claimer_email, u.student_id as claimer_student_id, u.department as claimer_dept
            FROM claims c
            JOIN items i ON c.item_id = i.id
            JOIN users u ON c.claimer_id = u.id
            WHERE c.id = ?
        """, (claim_id,), one=True)

    @staticmethod
    def get_by_item(item_id):
        return query_db("""
            SELECT c.*, u.name as claimer_name, u.email as claimer_email, u.student_id as claimer_student_id, u.department as claimer_dept
            FROM claims c
            JOIN users u ON c.claimer_id = u.id
            WHERE c.item_id = ?
            ORDER BY c.created_at DESC
        """, (item_id,))

    @staticmethod
    def get_by_user(user_id):
        return query_db("""
            SELECT c.*, 
                   i.title as item_title, i.item_type, i.status as item_status, i.location as item_location, i.category as item_category, i.image_path as item_image
            FROM claims c
            JOIN items i ON c.item_id = i.id
            WHERE c.claimer_id = ?
            ORDER BY c.created_at DESC
        """, (user_id,))

    @staticmethod
    def get_all(status=None):
        if status and status != 'All':
            return query_db("""
                SELECT c.*, 
                       i.title as item_title, i.item_type, i.status as item_status, i.location as item_location,
                       u.name as claimer_name, u.email as claimer_email, u.student_id as claimer_student_id, u.department as claimer_dept
                FROM claims c
                JOIN items i ON c.item_id = i.id
                JOIN users u ON c.claimer_id = u.id
                WHERE c.status = ?
                ORDER BY c.created_at DESC
            """, (status,))
        return query_db("""
            SELECT c.*, 
                   i.title as item_title, i.item_type, i.status as item_status, i.location as item_location,
                   u.name as claimer_name, u.email as claimer_email, u.student_id as claimer_student_id, u.department as claimer_dept
            FROM claims c
            JOIN items i ON c.item_id = i.id
            JOIN users u ON c.claimer_id = u.id
            ORDER BY c.created_at DESC
        """)

    @staticmethod
    def has_pending_claim(item_id, claimer_id):
        row = query_db("""
            SELECT id FROM claims 
            WHERE item_id = ? AND claimer_id = ? AND status = 'Pending'
        """, (item_id, claimer_id), one=True)
        return row is not None

    @staticmethod
    def create(item_id, claimer_id, proof_description, proof_image=None, contact_phone=None):
        claim_id = execute_db("""
            INSERT INTO claims (item_id, claimer_id, proof_description, proof_image, contact_phone, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
        """, (item_id, claimer_id, proof_description.strip(), proof_image, contact_phone.strip() if contact_phone else None))
        
        # Automatically update the item status to 'Claim Pending' if it was 'Found'
        execute_db("""
            UPDATE items SET status = 'Claim Pending', updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND status = 'Found'
        """, (item_id,))
        return claim_id

    @staticmethod
    def update_status(claim_id, status, admin_remarks=None):
        claim = ClaimModel.get_by_id(claim_id)
        if not claim:
            return False

        execute_db("""
            UPDATE claims 
            SET status = ?, admin_remarks = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, admin_remarks.strip() if admin_remarks else None, claim_id))

        if status == 'Approved':
            # Mark the item as 'Returned'
            execute_db("""
                UPDATE items SET status = 'Returned', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (claim['item_id'],))
            # Reject any other pending claims for this same item
            execute_db("""
                UPDATE claims SET status = 'Rejected', admin_remarks = 'Another claim was approved for this item.', updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ? AND id != ? AND status = 'Pending'
            """, (claim['item_id'], claim_id))
        elif status == 'Rejected':
            # Check if there are any other pending claims for this item
            other_pending = query_db("""
                SELECT COUNT(*) as cnt FROM claims WHERE item_id = ? AND status = 'Pending'
            """, (claim['item_id'],), one=True)
            if other_pending and other_pending['cnt'] == 0:
                # Revert item status back to 'Found'
                execute_db("""
                    UPDATE items SET status = 'Found', updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND status = 'Claim Pending'
                """, (claim['item_id'],))
        return True


class StatsModel:
    @staticmethod
    def get_system_stats():
        total_lost = query_db("SELECT COUNT(*) as count FROM items WHERE item_type = 'lost'", one=True)['count']
        total_found = query_db("SELECT COUNT(*) as count FROM items WHERE item_type = 'found'", one=True)['count']
        total_returned = query_db("SELECT COUNT(*) as count FROM items WHERE status = 'Returned'", one=True)['count']
        pending_claims = query_db("SELECT COUNT(*) as count FROM claims WHERE status = 'Pending'", one=True)['count']
        total_users = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'student'", one=True)['count']
        total_items = total_lost + total_found

        recovery_rate = round((total_returned / total_items * 100), 1) if total_items > 0 else 0.0

        return {
            'total_lost': total_lost,
            'total_found': total_found,
            'total_returned': total_returned,
            'pending_claims': pending_claims,
            'total_users': total_users,
            'total_items': total_items,
            'recovery_rate': recovery_rate
        }

    @staticmethod
    def get_user_stats(user_id):
        my_lost = query_db("SELECT COUNT(*) as count FROM items WHERE user_id = ? AND item_type = 'lost'", (user_id,), one=True)['count']
        my_found = query_db("SELECT COUNT(*) as count FROM items WHERE user_id = ? AND item_type = 'found'", (user_id,), one=True)['count']
        my_claims = query_db("SELECT COUNT(*) as count FROM claims WHERE claimer_id = ?", (user_id,), one=True)['count']
        my_pending_claims = query_db("SELECT COUNT(*) as count FROM claims WHERE claimer_id = ? AND status = 'Pending'", (user_id,), one=True)['count']
        my_approved_claims = query_db("SELECT COUNT(*) as count FROM claims WHERE claimer_id = ? AND status = 'Approved'", (user_id,), one=True)['count']

        return {
            'my_lost': my_lost,
            'my_found': my_found,
            'my_claims': my_claims,
            'my_pending_claims': my_pending_claims,
            'my_approved_claims': my_approved_claims
        }
