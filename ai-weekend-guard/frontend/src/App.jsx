import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get('http://localhost:5000/api/logs');
        setLogs(res.data);
        const lastLog = res.data[res.data.length - 1];
        if (lastLog.includes('ERROR') || lastLog.includes('Exception')) {
          setError(lastLog);
        }
      } catch (err) {
        console.error("Error fetching logs:", err);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); // poll every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleFixClick = () => {
    if (error) {
      window.location.href = '/fix';
    }
  };

  return (
    <div className="App">
      <h1>AI Weekend Support Agent</h1>
      <h2>Log Monitor</h2>
      <div className="logs">
        {logs.map((log, idx) => (
          <p key={idx} className={log.includes('ERROR') ? 'error' : ''}>
            {log}
          </p>
        ))}
      </div>

      {error && (
        <div className="suggestion-box">
          <h3>🚨 Error Detected:</h3>
          <p>{error}</p>
          <button onClick={handleFixClick}>Ask AI for Fix</button>
        </div>
      )}
    </div>
  );
}

export default App;