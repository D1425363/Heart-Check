import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Retrieve configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', '1') == '1'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
