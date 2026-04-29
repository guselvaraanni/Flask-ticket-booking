from flask import Flask, app, jsonify
from flasgger import Flasgger
from app.config import config_by_name
from app.extensions import db, migrate
from app.routes import events_bp, bookings_bp

def create_app(config_name='development'):
    """
    Application factory pattern.
    Creates and configures a Flask application.
    """
    app = Flask(__name__)
    
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
    
    # Register blueprints
    app.register_blueprint(events_bp)
    app.register_blueprint(bookings_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'message': 'API is running'}), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def index():
        """API root - redirects to docs"""
        return jsonify({
            'message': 'Welcome to the Seat Booking API',
            'docs': '/apidocs',
            'version': '1.0.0'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
