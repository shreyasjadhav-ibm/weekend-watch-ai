from flask import Flask, render_template, request, jsonify, Response
import logging
import random
import os
import google.generativeai as genai
from queue import Queue
import json
import time
import re

app = Flask(__name__)

# Configure logging
logger = logging.getLogger('backend')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setFormatter(logging.Formatter('%(asctime)sZ,%(name)s,%(message)s'))
logger.addHandler(handler)

# SSE queue for anomaly alerts
alert_queue = Queue()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key')  # Replace with your key or use env var
genai.configure(api_key=GEMINI_API_KEY)

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
    if random.random() < 0.3:
        logger.error('MemoryError: Unable to allocate memory,MemoryError')
        raise MemoryError('Unable to allocate memory')
    logger.info('Request processed in 120ms,None')
    return jsonify({'data': 'sample'})

@app.route('/log-error', methods=['POST'])
def log_error():
    error_data = request.json
    logger.error(f"[ALERT] {error_data['message']},{error_data['error_type']}")
    alert_queue.put(error_data)
    return jsonify({'status': 'logged'})

@app.route('/alerts')
def alerts():
    def stream():
        while True:
            if not alert_queue.empty():
                log = alert_queue.get()
                yield f"data: {json.dumps(log)}\n\n"
            time.sleep(0.1)
    return Response(stream(), mimetype='text/event-stream')

@app.route('/suggest-fix', methods=['POST'])
def suggest_fix():
    log = request.json
    try:
        with open('static/script.js', 'r') as f:
            code = f.read()
        prompt = f"""
        Error: {log['message']}
        Error Type: {log['error_type']}
        Source: {log['source']}
        Code:
        {code}

        Suggest a fix for the JavaScript error, focusing on the faulty function. Provide the corrected function code in a ```javascript block. Example:
        ```javascript
        function correctedFunction() {{
            // Corrected code
        }}
        ```
        """
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        suggestion = response.text
        # Extract code block
        code_match = re.search(r'```javascript\n([\s\S]*?)\n```', suggestion)
        extracted_code = code_match.group(1) if code_match else ''
        return jsonify({
            'suggestion': suggestion,
            'extracted_code': extracted_code
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/apply-fix', methods=['POST'])
def apply_fix():
    try:
        data = request.json
        extracted_code = data.get('extracted_code')
        if not extracted_code:
            return jsonify({'error': 'No code provided'}), 400
        # Read script.js and replace the faulty function
        with open('static/script.js', 'r') as f:
            current_code = f.read()
        # Assume the function to replace is 'brokenSyntax' for now
        # Use regex to replace the function (simplified for brokenSyntax)
        new_code = re.sub(
            r'function brokenSyntax\(\) \{[\s\S]*?\}',
            extracted_code,
            current_code
        )
        # Save the updated code
        with open('static/script.js', 'w') as f:
            f.write(new_code)
        return jsonify({'status': 'Code updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)