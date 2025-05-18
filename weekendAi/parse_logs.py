import pandas as pd
import re

logs = []
with open('app.log', 'r') as f:
    for line in f:
        match = re.match(r'(\S+),(\w+),(.+?)(?:,(\w+))?$', line)
        if match:
            timestamp, source, message, error_type = match.groups()
            if error_type is None and ',' in message:
                message, error_type = message.rsplit(',', 1)
            label = 1 if error_type and error_type != 'None' else 0
            logs.append({
                'timestamp': timestamp,
                'source': source,
                'message': message.strip(),
                'error_type': error_type if error_type else 'None',
                'label': label
            })

df = pd.DataFrame(logs)
df.to_csv('logs_expanded.csv', index=False)
print(f"Saved {len(df)} logs to logs_expanded.csv")