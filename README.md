# 🎓 UniFind Campus - Lost and Found Management System

A production-grade, full-stack web application designed for college campuses to streamline reporting missing belongings, logging found items, submitting ownership claims with verifiable proof, and moderating returns through campus security.

Built with **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript**.

---

## 🌟 Key Features

1. **Modern Responsive UI/UX**:
   - Polished design tailored for universities with smooth animations, Inter typography, glassmorphism navigation, and responsive mobile layouts.
   - Dynamic SVG icons, custom drag-and-drop file upload zones with instant image previews, and floating toast notifications.

2. **Authentication & Authorization**:
   - Secure student registration with Department and Student ID verification.
   - Dual-mode login (login with either College Email or Student ID).
   - Password hashing with Werkzeug (`pbkdf2:sha256`).
   - Role-Based Access Control (`student` vs `admin`) with route decorators.

3. **Student Dashboard & Profile**:
   - Real-time personal activity metrics (My Lost Items, My Found Reports, My Claims, Reunited Items).
   - Tabbed view to manage your listings and monitor claim verification statuses.
   - Profile management with department updates and password changes.

4. **Lost Item Reporting**:
   - Submit item name, category, detailed description, campus building location, date lost, photo upload, and preferred contact info.

5. **Found Item Reporting**:
   - Log discovered items with campus location, date found, custody / safe holding desk details, and optional photo.

6. **Catalog Browsing & Granular Filters**:
   - Live full-text search across item names, descriptions, and locations.
   - Filter by listing type (`All`, `Lost Items`, `Found Items`), category, campus location, and current item status.

7. **Secure Claim Submission & Verification**:
   - Students can claim found belongings by supplying unique proof of ownership (e.g., hidden marks, screen lock wallpaper, serial number fragments, purchase receipt).
   - System prevents students from fraudulently claiming their own found items or items already returned.

8. **Campus Administrator Control Center (`/admin`)**:
   - Centralized moderation queue to review ownership claims with one-click **Approve** or **Reject** (with custom staff remarks).
   - Automatically marks items as `Returned` upon approval and safely rejects conflicting claims.
   - Quick status manager for all campus listings (`Lost`, `Found`, `Claim Pending`, `Returned`, `Closed`).
   - Registered student user management with role toggling (Student ↔ Admin).
   - Live system activity and audit trail logs.

---

## 📁 Project Directory Structure

```
campus_lost_found/
├── app.py                   # Main Flask application entry point
├── config.py                # Configuration settings, categories & locations
├── database.py              # SQLite database connection & table initialization
├── models.py                # Data access models (User, Item, Claim, Stats)
├── requirements.txt         # Project dependencies
├── test_app.py              # Automated unit and integration test suite
├── README.md                # Comprehensive documentation
├── routes/
│   ├── __init__.py          # Auth decorators (@login_required, @admin_required) & file upload handlers
│   ├── auth.py              # User registration, login, session, and logout
│   ├── items.py             # Browse, search, filter, report lost & found, item details
│   ├── claims.py            # Submit claims, ownership proof, claim tracking
│   ├── user.py              # Student dashboard, user profile & settings
│   └── admin.py             # Administrator dashboard, claim approval/rejection, user management
├── static/
│   ├── css/
│   │   └── style.css        # Master responsive stylesheet (Design system tokens, cards, tables, forms)
│   ├── js/
│   │   └── script.js        # Mobile toggle, instant image previews, tab switching, modals
│   └── images/
│       ├── logo.svg         # Official UniFind vector logo
│       └── placeholder.svg  # High-quality fallback placeholder image
├── templates/
│   ├── base.html            # Master layout with navbar, alerts, footer & modals
│   ├── index.html           # Landing home page with hero, live stats, how it works, features
│   ├── login.html           # Login page with demo account auto-fill buttons
│   ├── register.html        # Student registration form
│   ├── dashboard.html       # Student personalized control center
│   ├── report_lost.html     # Report lost item form with drag & drop photo upload
│   ├── report_found.html    # Report found item form with custody details
│   ├── browse_items.html    # Search, filter, and responsive item grid
│   ├── item_details.html    # Complete item view, specifications & claims list
│   ├── claim_item.html      # Ownership claim submission form with verification guide
│   ├── profile.html         # User profile, password reset & my listings
│   ├── admin_dashboard.html # Admin panel for claims moderation & user management
│   └── 404.html             # Custom error 404 page
├── uploads/                 # Storage for user-uploaded item and proof photos
└── instance/
    └── database.db          # SQLite database (auto-created on first run)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure **Python 3.10+** is installed on your computer.

### 2. Navigate to the Project Folder
```bash
cd "C:\Users\Anvi\.gemini\antigravity\scratch\campus_lost_found"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Website
```bash
python app.py
```
*(On systems with multiple Python versions, use `py -3 app.py` or the direct path to your Python executable).*

### 5. Open in Your Browser
Visit:
```
http://127.0.0.1:5000
```
or
```
http://localhost:5000
```

---

## 🔑 Pre-Seeded Test Accounts

The system automatically initializes and seeds default accounts and sample campus listings on first launch:

### 🛡️ Campus Administrator Account
- **Email:** `admin@campus.edu`
- **Password:** `AdminPassword123!`
- **Role:** Administrator (Campus Safety & Security)
- **Permissions:** Full access to `/admin` control center, claim approval/rejection, item status updates, and user moderation.

### 🎓 Demo Student Account 1
- **Email:** `alex.student@campus.edu` (or login using Student ID: `CS-2024-042`)
- **Password:** `StudentPassword123!`
- **Role:** Student (Computer Science & Engineering)

### 🎓 Demo Student Account 2
- **Email:** `sarah.mitchell@campus.edu` (or login using Student ID: `ENG-2023-118`)
- **Password:** `StudentPassword123!`
- **Role:** Student (Electrical & Electronics Engineering)

*(Note: The login page also includes 1-click test credential fill buttons for fast evaluation!)*

---

## 🧪 Running Automated Tests

A complete automated unit and integration test suite is included in `test_app.py`:
```bash
python -m unittest test_app.py
```
All 11 test suites verify:
- Home page rendering & live statistics.
- Student registration, duplicate prevention, and validation.
- Authentication with email or Student ID.
- Student dashboard metrics.
- Reporting lost items with image uploads.
- Reporting found items with custody locations.
- Catalog browsing, multi-category filtering, and keyword search.
- Item details view.
- Claim submission, duplicate claim blocking, and self-claim prevention.
- Administrator route protection, claim approvals, and automatic item status transitions to `Returned`.
- Student profile updates and password changes.
