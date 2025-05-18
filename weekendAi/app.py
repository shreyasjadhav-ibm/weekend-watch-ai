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
def landing():
    logger.info('GET /landing 200 OK,None')
    return render_template('landing.html')

@app.route('/login')
def login_page():
    logger.info('GET /login 200 OK,None')
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

You are an expert JavaScript debugger tasked with fixing a JavaScript error in the provided code. Follow these steps:
1. Analyze the error message, type, and source to identify the root cause (e.g., syntax error in a function, undefined variable).
2. Locate the affected code section (function, variable, or statement) in the provided code.
3. Apply the minimal changes needed to fix the error, preserving all other code (e.g., other functions, event listeners) exactly as is.
4. If the user suggestion is provided (e.g., 'remove the whole block', 'fix only the parenthesis'), incorporate it into the fix:
   - 'remove the whole block': Delete the faulty function or code block if safe.
   - 'fix only the parenthesis': Correct only the syntax issue.
   - Other suggestions: Adapt the fix to align with the user's intent.
5. If no user suggestion is provided, apply the most straightforward fix.
6. Output the entire corrected code for the file, including all unchanged parts, in a ```javascript block.
7. Ensure the output is valid JavaScript, maintaining original formatting and comments where possible.

Example output:
```javascript
// Original code with other functions
function otherFunction() {{
    console.log('Unchanged');
}}
// Corrected function
function faultyFunction() {{
    console.log('Fixed');
}}
Do not add explanations outside the code block unless requested. Only return the ```javascript block with the full corrected code.
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
            logger.error('No code provided for fix,None')
            return jsonify({'error': 'No code provided'}), 400
        # Validate code (basic check for non-empty JavaScript)
        if not extracted_code.strip() or 'function' not in extracted_code:
            logger.error('Invalid JavaScript code provided,None')
            return jsonify({'error': 'Invalid JavaScript code'}), 400
        # Overwrite script.js with the full corrected code
        with open('static/script.js', 'w') as f:
            f.write(extracted_code)
        logger.info('Code fix applied successfully,None')
        return jsonify({'status': 'Code updated successfully'})
    except IOError as e:
        logger.error(f'File write error: {str(e)},IOError')
        return jsonify({'error': f'Failed to write file: {str(e)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error in apply-fix: {str(e)},{type(e).__name__}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)