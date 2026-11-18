import os
from flask import Flask, render_template, send_from_directory, session, request, redirect, url_for
from config import Config
from database import close_db, init_db, query_db
from models import StatsModel, ItemModel, ClaimModel
from routes.auth import auth_bp
from routes.items import items_bp
from routes.claims import claims_bp
from routes.user import user_bp
from routes.admin import admin_bp
from datetime import datetime

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Register database teardown
    app.teardown_appcontext(close_db)

    # Initialize database tables and seed data automatically
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Context processors for global template variables
    @app.context_processor
    def inject_global_data():
        pending_claims_badge = 0
        if session.get('user_role') == 'admin':
            row = query_db("SELECT COUNT(*) as cnt FROM claims WHERE status = 'Pending'", one=True)
            pending_claims_badge = row['cnt'] if row else 0

        user_claims_badge = 0
        if session.get('user_id'):
            row = query_db("SELECT COUNT(*) as cnt FROM claims WHERE claimer_id = ? AND status = 'Pending'", (session.get('user_id'),), one=True)
            user_claims_badge = row['cnt'] if row else 0

        return {
            'admin_pending_claims_count': pending_claims_badge,
            'user_pending_claims_count': user_claims_badge,
            'current_year': datetime.now().year,
            'categories_list': Config.CATEGORIES,
            'locations_list': Config.LOCATIONS
        }

    # Custom template filters
    @app.template_filter('format_date')
    def format_date(value, format_str='%b %d, %Y'):
        if not value:
            return ''
        try:
            if isinstance(value, str):
                # Try parsing ISO date or datetime
                for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                    try:
                        dt = datetime.strptime(value.split('.')[0], fmt)
                        return dt.strftime(format_str)
                    except ValueError:
                        continue
                return value
            elif isinstance(value, (datetime, )):
                return value.strftime(format_str)
            return str(value)
        except Exception:
            return str(value)

    @app.template_filter('status_badge')
    def status_badge(status):
        badges = {
            'Lost': 'badge-danger',
            'Found': 'badge-success',
            'Claim Pending': 'badge-warning',
            'Returned': 'badge-info',
            'Closed': 'badge-secondary'
        }
        return badges.get(status, 'badge-light')

    # Serve uploads
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Home route
    @app.route('/')
    def index():
        stats = StatsModel.get_system_stats()
        recent_items = ItemModel.get_recent(limit=6)
        return render_template(
            'index.html',
            stats=stats,
            recent_items=recent_items,
            categories=Config.CATEGORIES
        )

    # 404 Error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # 500 Error handler
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('404.html', error_title="Server Error", error_msg="Something went wrong on our end. Please try again later."), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Run the web application
    app.run(host='0.0.0.0', port=5000, debug=True)
