document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    try {
        // Simulate JS error randomly
        if (Math.random() < 0.2) {
            myUndefinedFunction(); // Causes ReferenceError
        }
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        fetch('/log-error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: 'frontend',
                message: error.message,
                error_type: error.name
            })
        });
    }
});

// Intentional syntax error for testing
function brokenSyntax() {
    console.log("This is broken" )}// Missing closing parenthesis and brace

// SSE for anomaly alerts
const source = new EventSource('/alerts');
source.onmessage = function(event) {
    const log = JSON.parse(event.data);
    const modal = document.getElementById('alert-modal');
    const message = document.getElementById('alert-message');
    message.textContent = `Anomaly detected: ${log.message} (${log.error_type})`;
    modal.style.display = 'block';

    // Handle Yes/No buttons
    const yesBtn = document.getElementById('suggest-yes');
    const noBtn = document.getElementById('suggest-no');
    
    yesBtn.onclick = async () => {
        const response = await fetch('/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(log)
        });
        const data = await response.json();
        if (data.suggestion) {
            alert(`Suggested Fix: ${data.suggestion}`);
        } else {
            alert(`Error: ${data.error}`);
        }
        modal.style.display = 'none';
    };
    
    noBtn.onclick = () => {
        modal.style.display = 'none';
    };
};