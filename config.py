import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campus-lost-found-super-secret-key-2026-prod-dev')
    DATABASE_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 Megabytes max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Campus specific constants
    CATEGORIES = [
        'Electronics & Gadgets',
        'Wallets & Purses',
        'Keys & Access Cards',
        'Books & Stationery',
        'ID Cards & Documents',
        'Clothing & Accessories',
        'Bags & Backpacks',
        'Sports & Fitness',
        'Water Bottles & Containers',
        'Eyewear & Glasses',
        'Other'
    ]

    LOCATIONS = [
        'Main Library',
        'Student Center / Cafeteria',
        'Science Block A',
        'Science Block B',
        'Engineering Building',
        'Sports Complex & Gym',
        'University Auditorium',
        'Administrative Block',
        'Campus Parking Lot',
        'Hostel / Dormitory Quad',
        'Main Campus Gate & Bus Stop',
        'Computer & Tech Labs',
        'Other / Outdoor Grounds'
    ]

    DEPARTMENTS = [
        'Computer Science & Engineering',
        'Information Technology',
        'Electrical & Electronics Engineering',
        'Mechanical Engineering',
        'Civil Engineering',
        'Business Administration',
        'Biotechnology & Life Sciences',
        'Arts, Humanities & Design',
        'Physics & Mathematics',
        'Medicine & Health Sciences',
        'Law & Public Policy',
        'Other'
    ]

    ITEM_STATUSES = [
        'Lost',
        'Found',
        'Claim Pending',
        'Returned',
        'Closed'
    ]
