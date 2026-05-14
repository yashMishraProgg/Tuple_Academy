"""
middleware.py — CORS headers + global error handlers
"""

from flask import jsonify, request


def cors_middleware(app):
    """Add CORS headers to every response (replaces flask-cors)."""

    @app.after_request
    def add_cors(response):
        origin = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin']  = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            from flask import make_response
            resp = make_response()
            resp.headers['Access-Control-Allow-Origin']  = request.headers.get('Origin', '*')
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            return resp


def error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'message': 'Valid token required'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'message': str(e)}), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'error': 'Conflict', 'message': str(e)}), 409

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
