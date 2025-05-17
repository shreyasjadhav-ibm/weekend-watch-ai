import pickle
import pandas as pd
import numpy as np
import time
import re
import requests

# Load model and preprocessors
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('tfidf.pkl', 'rb') as f:
        tfidf = pickle.load(f)
    with open('encoder.pkl', 'rb') as f:
        encoder = pickle.load(f)
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure model.pkl, tfidf.pkl, and encoder.pkl are in the directory.")
    exit(1)

# Suggestion engine
def get_suggestion(log):
    suggestions = {
        'ReferenceError': 'Check if the variable or function is defined in your JavaScript code.',
        'ValidationError': 'Verify the input format (e.g., email) in your form validation.',
        'MemoryError': 'Reduce memory usage or check server resource limits.',
        'TypeError': 'Ensure the variable type is correct or handle None values.',
        'ValueError': 'Check input data for correct format or values.',
        'SyntaxError': 'Check for missing parentheses, braces, or other syntax issues in your JavaScript code.'
    }
    error_type = log['error_type']
    return suggestions.get(error_type, 'No specific fix available. Check the log message for details.')

# Predict a log
def predict_log(log):
    df_log = pd.DataFrame([log])
    df_log['error_type'] = df_log['error_type'].fillna('None')
    message_vec = tfidf.transform(df_log['message']).toarray()
    cat_vec = encoder.transform(df_log[['source', 'error_type']])
    features = np.concatenate([message_vec, cat_vec], axis=1)
    prediction = model.predict(features)[0]
    return 'Anomaly' if prediction == 1 else 'Normal'

# Send alert
def send_alert(log, prediction):
    if prediction == 'Anomaly':
        suggestion = get_suggestion(log)
        print(f"🚨 ALERT: Anomaly detected! Source: {log['source']}, Message: {log['message']}, Error Type: {log['error_type']}")
        print(f"Suggestion: {suggestion}")
        # Push to Flask for frontend alert
        try:
            requests.post('http://localhost:5001/log-error', json=log)
        except requests.RequestException as e:
            print(f"Failed to push alert to frontend: {e}")

# Monitor log file
def monitor_logs(log_file):
    try:
        with open(log_file, 'r') as f:
            f.seek(0, 2)
            print(f"Monitoring {log_file}...")
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}Z),(\w+),(.+?)(?:,(\w+))?$', line)
                if match:
                    timestamp, source, message, error_type = match.groups()
                    if source == 'werkzeug':
                        print(f"Skipped Werkzeug log: {line.strip()}")
                        continue
                    if error_type is None and ',' in message:
                        message, error_type = message.rsplit(',', 1)
                    log = {
                        'source': source,
                        'message': message.strip(),
                        'error_type': error_type if error_type else 'None'
                    }
                    prediction = predict_log(log)
                    print(f"[{timestamp}] {source}: {message} -> {prediction}")
                    send_alert(log, prediction)
                else:
                    print(f"Skipped unparseable log: {line.strip()}")
    except FileNotFoundError:
        print(f"Error: {log_file} not found. Ensure app.py is generating logs.")
        exit(1)

if __name__ == '__main__':
    monitor_logs('app.log')