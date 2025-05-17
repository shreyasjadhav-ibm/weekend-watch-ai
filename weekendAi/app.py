from flask import Flask, render_template, request, jsonify
import logging
import random

app = Flask(__name__)

# Configure logging
logger = logging.getLogger('backend')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setFormatter(logging.Formatter('%(asctime)sZ,%(name)s,%(message)s'))
logger.addHandler(handler)

@app.route('/')
def home():
    logger.info('GET /home 200 OK,None')
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data.get('email'):
            raise ValueError('Invalid email')
        logger.info('POST /login successful,None')
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Login failed: {str(e)},{type(e).__name__}')
        return jsonify({'error': str(e)}), 400

@app.route('/api/data')
def data():
    # Simulate random errors
    if random.random() < 0.3:
        logger.error('MemoryError: Unable to allocate memory,MemoryError')
        raise MemoryError('Unable to allocate memory')
    logger.info('Request processed in 120ms,None')
    return jsonify({'data': 'sample'})

@app.route('/log-error', methods=['POST'])
def log_error():
    error_data = request.json
    logger.error(f"{error_data['message']},{error_data['error_type']}")
    return jsonify({'status': 'logged'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)