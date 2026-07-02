import os
import logging
from app import app

# 1. Professional Logging: Always know if your server started or why it failed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_server():
    """Starts the Flask server with safety and configuration checks."""
    
    # 2. Flexible Configuration: Use environment variables, default to safe values
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    if debug_mode:
        logging.warning("System is in DEBUG mode. Disable this in a live shop environment!")

    try:
        logging.info(f"Launching Dejar Auto Spares POS on port {port}...")
        # 3. Network Binding: 0.0.0.0 allows tablets/phones in your shop to connect
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        logging.error(f"Failed to start the application: {e}")

if __name__ == '__main__':
    start_server()