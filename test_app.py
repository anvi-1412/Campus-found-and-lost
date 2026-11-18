import os
import io
import tempfile
import unittest
from app import create_app
from database import init_db, get_db
from models import UserModel, ItemModel, ClaimModel, StatsModel

class CampusLostFoundTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for test isolation
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE_PATH': self.db_path,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # 1. Home Page Test
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'UniFind', response.data)
        self.assertIn(b'Report Lost Item', response.data)
        self.assertIn(b'Report Found Item', response.data)
        self.assertIn(b'Browse Items', response.data)

    # 2. Student Registration Test
    def test_student_registration(self):
        # Register a new student
        response = self.client.post('/register', data={
            'name': 'Taylor Swift',
            'email': 'taylor.student@campus.edu',
            'student_id': 'ART-2024-099',
            'department': 'Arts, Humanities & Design',
            'phone': '555-019-3321',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

        # Verify duplicate registration fails
        dup_response = self.client.post('/register', data={
            'name': 'Taylor Clone',
            'email': 'taylor.student@campus.edu',
            'student_id': 'ART-2024-099',
            'department': 'Arts, Humanities & Design',
            'phone': '555-019-3321',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        }, follow_redirects=True)
        self.assertIn(b'already exists', dup_response.data)

    # 3. Student Login & Logout Test
    def test_student_login_and_logout(self):
        # Login with email
        response = self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, Alex Rivera', response.data)

        # Logout
        logout_response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b'logged out successfully', logout_response.data)

        # Login with Student ID
        id_login = self.client.post('/login', data={
            'identifier': 'CS-2024-042',
            'password': 'StudentPassword123!'
        }, follow_redirects=True)
        self.assertEqual(id_login.status_code, 200)
        self.assertIn(b'Welcome back, Alex Rivera', id_login.data)

    # 4. Student Dashboard Test
    def test_student_dashboard(self):
        # Must redirect if not logged in
        res_guest = self.client.get('/dashboard')
        self.assertEqual(res_guest.status_code, 302)

        # Login as student
        self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        })
        res_logged = self.client.get('/dashboard')
        self.assertEqual(res_logged.status_code, 200)
        self.assertIn(b'Welcome, Alex Rivera', res_logged.data)
        self.assertIn(b'CS-2024-042', res_logged.data)

    # 5. Report Lost Item Test
    def test_report_lost_item(self):
        # Login
        self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        })

        # Submit lost item with dummy image upload
        image_data = io.BytesIO(b"fake image data for testing")
        response = self.client.post('/report/lost', data={
            'title': 'iPad Pro 11-inch with Apple Pencil',
            'category': 'Electronics & Gadgets',
            'description': 'Left on the 3rd floor sofa in the student center. Space grey color with magnetic pencil.',
            'location': 'Student Center / Cafeteria',
            'event_date': '2026-11-17',
            'contact_info': 'alex.student@campus.edu',
            'image': (image_data, 'test_ipad.png')
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your lost item report has been published', response.data)
        self.assertIn(b'iPad Pro 11-inch with Apple Pencil', response.data)

    # 6. Report Found Item Test
    def test_report_found_item(self):
        # Login
        self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        })

        response = self.client.post('/report/found', data={
            'title': 'Set of Dorm Keys with Green Tag',
            'category': 'Keys & Access Cards',
            'description': 'Found near the drinking fountain in Science Block A.',
            'location': 'Science Block A',
            'event_date': '2026-11-17',
            'custody_info': 'Handed to Science Department Secretary Room 101',
            'contact_info': 'alex.student@campus.edu'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The found item report has been posted', response.data)
        self.assertIn(b'Set of Dorm Keys with Green Tag', response.data)

    # 7. Browse, Search & Filter Items Test
    def test_browse_and_filter(self):
        # Browse all
        res_all = self.client.get('/browse')
        self.assertEqual(res_all.status_code, 200)
        self.assertIn(b'Browse Campus Listings', res_all.data)

        # Filter by type lost
        res_lost = self.client.get('/browse?type=lost')
        self.assertEqual(res_lost.status_code, 200)

        # Filter by category
        res_cat = self.client.get('/browse?category=Electronics+%26+Gadgets')
        self.assertEqual(res_cat.status_code, 200)

        # Search query
        res_search = self.client.get('/browse?search=MacBook')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'MacBook Air', res_search.data)

    # 8. Item Details View Test
    def test_item_details(self):
        response = self.client.get('/items/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Space Grey MacBook Air M2', response.data)

    # 9. Claim Submission Test & Prevention of Self-Claiming
    def test_claim_submission(self):
        # Sarah reported Sony Headphones (item id 3). Alex tries to claim it.
        self.client.post('/login', data={
            'identifier': 'sarah.mitchell@campus.edu',
            'password': 'StudentPassword123!'
        })
        # Sarah shouldn't be able to claim her own found item (item 3)
        self_claim_res = self.client.post('/claim/3', data={
            'proof_description': 'This is my own item that I found.',
            'contact_phone': '555-017-4482'
        }, follow_redirects=True)
        self.assertIn(b'You cannot claim an item that you reported', self_claim_res.data)

        # Item 4 was reported by admin. Sarah claims item 4 (Subaru car key).
        claim_res = self.client.post('/claim/4', data={
            'proof_description': 'The key has a blue lanyard and a grocery club barcode card attached on the ring.',
            'contact_phone': '555-017-4482'
        }, follow_redirects=True)
        self.assertEqual(claim_res.status_code, 200)
        self.assertIn(b'Claim submitted successfully', claim_res.data)

    # 10. Admin Portal Protection & Admin Actions
    def test_admin_portal_and_claim_approval(self):
        # Regular student tries to access admin -> blocked
        self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        })
        admin_blocked = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied', admin_blocked.data)

        # Admin logs in
        self.client.get('/logout')
        admin_login = self.client.post('/login', data={
            'identifier': 'admin@campus.edu',
            'password': 'AdminPassword123!'
        }, follow_redirects=True)
        self.assertEqual(admin_login.status_code, 200)
        self.assertIn(b'Administrator Control Center', admin_login.data)

        # Approve the pre-seeded claim #1 (Alex claiming Sony headphones #3)
        approve_res = self.client.post('/admin/claims/1/action', data={
            'action': 'approve',
            'admin_remarks': 'Verified Alex with student ID card CS-2024-042.'
        }, follow_redirects=True)
        self.assertIn(b'successfully marked as Approved', approve_res.data)

        # Verify item #3 status became 'Returned'
        with self.app.app_context():
            item = ItemModel.get_by_id(3)
            self.assertEqual(item['status'], 'Returned')

    # 11. Profile Update Test
    def test_user_profile_update(self):
        self.client.post('/login', data={
            'identifier': 'alex.student@campus.edu',
            'password': 'StudentPassword123!'
        })
        res = self.client.post('/profile/update', data={
            'name': 'Alexander Rivera Jr.',
            'department': 'Computer Science & Engineering',
            'phone': '555-999-8888'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Profile details updated successfully', res.data)

if __name__ == '__main__':
    unittest.main()
