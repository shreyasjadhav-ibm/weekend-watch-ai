from flask import Flask, render_template, request, jsonify, Response
import logging
import random
import os
import google.generativeai as genai
from queue import Queue
import json
import time
import re
import smtplib
import uuid
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

app = Flask(__name__)

# Configure logging
logger = logging.getLogger('backend')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setFormatter(logging.Formatter('%(asctime)sZ,%(name)s,%(message)s'))
logger.addHandler(handler)

# SSE queue for anomaly alerts
alert_queue = Queue()

# Store pending fixes {issue_id: {log, before_code, after_code, approved}}
pending_fixes = {}



# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key')  # Replace with your key
genai.configure(api_key=GEMINI_API_KEY)

def check_email_replies():
    """Periodically check for Y/N replies to approval emails."""
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
            mail.select('INBOX')
            logger.info('IMAP connected to check replies in INBOX,None')

            for issue_id in list(pending_fixes.keys()):
                if pending_fixes[issue_id]['approved']:
                    continue
                result, data = mail.search(None, f'(TEXT "{issue_id}")')
                if result != 'OK':
                    logger.error(f'IMAP search failed for issue {issue_id},None')
                    continue

                for num in data[0].split():
                    result, msg_data = mail.fetch(num, '(RFC822)')
                    if result != 'OK':
                        continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    email_subject = msg.get('Subject', '')
                    from_addr = msg.get('From', '').lower()
                    logger.info(f'Processing email for issue {issue_id}, subject: {email_subject}, from: {from_addr},None')

                    if DEVELOPER_EMAIL.lower() not in from_addr:
                        logger.info(f'Skipping email for issue {issue_id}, from address {from_addr} does not match {DEVELOPER_EMAIL},None')
                        continue

                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    body_lines = body.split('\n')
                    clean_body = ''
                    for line in body_lines:
                        if line.startswith('>') or line.startswith('On ') or 'wrote:' in line:
                            break
                        clean_body += line.strip() + '\n'
                    clean_body = clean_body.strip().lower()
                    logger.info(f'Parsed email body for issue {issue_id}: {clean_body},None')

                    if clean_body in ('y', 'n'):
                        pending_fixes[issue_id]['approved'] = (clean_body == 'y')
                        logger.info(f'Processed reply for issue {issue_id}: {clean_body},None')
                        if clean_body == 'y':
                            alert_queue.put({
                                'source': 'backend',
                                'message': f'Fix approved for issue {issue_id}',
                                'error_type': 'Approval'
                            })
                            logger.info(f'Sent SSE approval message for issue {issue_id},None')
                        mail.store(num, '+FLAGS', '\\Seen')
                        break
                if pending_fixes[issue_id]['approved']:
                    break

            mail.logout()
        except Exception as e:
            logger.error(f'IMAP check failed: {str(e)},{type(e).__name__}')
        time.sleep(10)

threading.Thread(target=check_email_replies, daemon=True).start()

@app.route('/')
def landing():
    logger.info('GET /landing 200 OK,None')
    return render_template('landing.html')

@app.route('/connectors')
def connectors_page():
    logger.info('GET /connectors 200 OK,None')
    return render_template('index.html')

@app.route('/run-connector', methods=['POST'])
def run_connector():
    try:
        data = request.json
        if not data.get('connector'):
            raise ValueError('Invalid connector name')
        logger.info('POST /run-connector successful,None')
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Connector run failed: {str(e)},{type(e).__name__}')
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
    user_suggestion = log.get('user_suggestion', '')
    try:
        try:
            with open('static/script.js', 'r') as f:
                before_code = f.read()
        except IOError as e:
            logger.error(f'Failed to read script.js: {str(e)},IOError')
            return jsonify({'error': 'Failed to read code file'}), 500

        fix_prompt = f"""
Error: {log['message']}
Error Type: {log['error_type']}
Source: {log['source']}
Code:
{before_code}
User Suggestion (optional): {user_suggestion}

You are an expert JavaScript debugger tasked with fixing a JavaScript error in the provided code. Follow these steps:
1. Analyze the error message, type, and source to identify the root cause (e.g., undefined variable).
2. Locate the affected code section in the provided code.
3. Apply the minimal changes needed to fix the error, preserving all other code exactly as is.
4. If the user suggestion is provided (e.g., 'initialize the connector'), incorporate it:
   - 'initialize the connector': Add missing function.
   - 'fix the configuration': Ensure proper configuration object.
   - Other suggestions: Adapt to user intent.
5. If no suggestion, apply the most straightforward fix.
6. Output the entire corrected code in a ```javascript block.
7. Ensure valid JavaScript, maintaining original formatting.

Example:
```javascript
function initializeConnector() {{
    console.log('Initialized');
}}
```
"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(fix_prompt)
            suggestion = response.text
            code_match = re.search(r'```javascript\n([\s\S]*?)\n```', suggestion)
            if not code_match:
                logger.error('Failed to extract code block from Gemini response,None')
                return jsonify({'error': 'Invalid Gemini response format'}), 500
            after_code = code_match.group(1)
        except Exception as e:
            logger.error(f'Gemini API failed: {str(e)},{type(e).__name__}')
            return jsonify({'error': f'Gemini API error: {str(e)}'}), 500

        email_prompt = f"""
Generate an email for a developer to approve a code fix. Include:
1. **Issue**: 2-line description of the error and fix.
2. **Before Code**: The original code.
3. **After Code**: The fixed code.
4. **GitHub-like Diff**: Show added (+) and removed (-) lines.
5. **Approval Instructions**: Reply with 'Y' to approve or 'N' to reject.

Input:
- Error: {log['message']}
- Error Type: {log['error_type']}
- Before Code:
{before_code}
- After Code:
{after_code}
- User Suggestion: {user_suggestion}

Output the email body as plain text.
"""
        try:
            email_response = model.generate_content(email_prompt)
            email_body = email_response.text
        except Exception as e:
            logger.error(f'Gemini email prompt failed: {str(e)},{type(e).__name__}')
            return jsonify({'error': f'Gemini email error: {str(e)}'}), 500

        issue_id = str(uuid.uuid4())
        logger.info(f'Generated issue_id: {issue_id} for error: {log["message"]},None')
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = DEVELOPER_EMAIL
        msg['Subject'] = f'Code Fix Approval Request - Issue {issue_id}'
        msg.attach(MIMEText(email_body, 'plain'))

        email_sent = False
        try:
            if EMAIL_SENDER == 'your-gmail-address@gmail.com' or EMAIL_PASSWORD == 'your-gmail-app-password':
                raise ValueError('Placeholder email credentials detected')
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, DEVELOPER_EMAIL, msg.as_string())
            server.quit()
            logger.info(f'Email sent to {DEVELOPER_EMAIL} for issue {issue_id},None')
            email_sent = True
        except Exception as e:
            logger.error(f'Email send failed: {str(e)},{type(e).__name__}')
            try:
                mock_file = f'email_mock_{issue_id}.txt'
                with open(mock_file, 'w') as f:
                    f.write(f"Subject: {msg['Subject']}\nTo: {DEVELOPER_EMAIL}\n\n{email_body}")
                logger.info(f'Mocked email saved to {mock_file} for issue {issue_id},None')
            except IOError as e:
                logger.error(f'Failed to save mock email: {str(e)},IOError')
                return jsonify({'error': f'Failed to mock email: {str(e)}'}), 500

        pending_fixes[issue_id] = {
            'log': log,
            'before_code': before_code,
            'after_code': after_code,
            'approved': True  # Hardcode approval for demo
        }
        logger.info(f'Pending fixes updated. Current issue IDs: {list(pending_fixes.keys())},None')

        return jsonify({
            'suggestion': suggestion,
            'extracted_code': after_code,
            'issue_id': issue_id,
            'email_sent': email_sent
        })
    except Exception as e:
        logger.error(f'Suggest-fix unexpected error: {str(e)},{type(e).__name__}')
        return jsonify({'error': str(e)}), 500

@app.route('/set-approval', methods=['POST'])
def set_approval():
    data = request.json
    issue_id = data.get('issue_id')
    approved = data.get('approved', False)
    logger.info(f'Attempting to set approval for issue_id: {issue_id},None')
    if issue_id not in pending_fixes:
        logger.error(f'Invalid issue ID: {issue_id}. Available IDs: {list(pending_fixes.keys())},None')
        return jsonify({'error': f'Invalid issue ID. Available IDs: {list(pending_fixes.keys())}'}), 400
    pending_fixes[issue_id]['approved'] = approved
    if approved:
        alert_queue.put({
            'source': 'backend',
            'message': f'Fix approved for issue {issue_id}',
            'error_type': 'Approval'
        })
        logger.info(f'Sent SSE approval message for issue {issue_id},None')
    else:
        logger.info(f'Rejection set for issue {issue_id},None')
    return jsonify({'status': 'updated'})

@app.route('/apply-fix', methods=['POST'])
def apply_fix():
    try:
        data = request.json
        extracted_code = data.get('extracted_code')
        issue_id = data.get('issue_id')
        if not extracted_code or not issue_id:
            logger.error('Missing code or issue ID,None')
            return jsonify({'error': 'Missing code or issue ID'}), 400
        if issue_id not in pending_fixes or not pending_fixes[issue_id]['approved']:
            logger.error('Fix not approved for issue,None')
            return jsonify({'error': 'Fix not approved by developer'}), 403
        if not extracted_code.strip() or 'function' not in extracted_code:
            logger.error('Invalid JavaScript code provided,None')
            return jsonify({'error': 'Invalid JavaScript code'}), 400
        with open('static/script.js', 'w') as f:
            f.write(extracted_code)
        logger.info('Code fix applied successfully,None')
        del pending_fixes[issue_id]
        return jsonify({'status': 'Code updated successfully'})
    except IOError as e:
        logger.error(f'File write error: {str(e)},IOError')
        return jsonify({'error': f'Failed to write file: {str(e)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error in apply-fix: {str(e)},{type(e).__name__}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)