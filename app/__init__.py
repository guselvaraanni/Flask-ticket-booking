import os
from flask import Flask, jsonify
from flasgger import Flasgger
from app.config import config_by_name
from app.extensions import db, migrate
from app.routes import events_bp, bookings_bp, pages_bp, demo_bp


def create_app(config_name='development'):
    """
    Application factory pattern.
    Creates and configures a Flask application.
    """
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app = Flask(
        __name__,
        template_folder=os.path.join(root, 'templates'),
        static_folder=os.path.join(root, 'static'),
    )
    
    # Load configuration
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Swagger/Flasgger
    app.config['SWAGGER'] = {
    'title': 'Seat Booking API',
    'uiversion': 3
    }
    Flasgger(app)
    
    # Register blueprints (API + UI)
    app.register_blueprint(events_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(demo_bp)

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

    @app.route('/api', methods=['GET'])
    def api_index():
        """API metadata for programmatic clients"""
        return jsonify({
            'message': 'Welcome to the Seat Booking API',
            'docs': '/apidocs',
            'ui': '/',
            'version': '1.0.0'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create tables and sync presentation columns on events (safe for existing DBs)
    with app.app_context():
        db.create_all()
        from app.schema_utils import ensure_event_presentation_columns
        ensure_event_presentation_columns()

    @app.template_filter('inr')
    def format_inr(value):
        """Format amount as Indian Rupees for templates."""
        try:
            amount = int(round(float(value or 0)))
        except (TypeError, ValueError):
            amount = 0
        return f'₹{amount:,}'

    return app
