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
    const recommendation = document.getElementById('recommendation');
    const initialButtons = document.getElementById('initial-buttons');
    const fixButtons = document.getElementById('fix-buttons');
    
    message.textContent = `Anomaly detected: ${log.message} (${log.error_type})`;
    recommendation.classList.add('hidden');
    recommendation.textContent = '';
    initialButtons.classList.remove('hidden');
    fixButtons.classList.add('hidden');
    modal.classList.add('show');

    // Handle Yes/No buttons
    const yesBtn = document.getElementById('suggest-yes');
    const noBtn = document.getElementById('suggest-no');
    const fixBtn = document.getElementById('fix-error');
    const closeBtn = document.getElementById('close-suggestion');
    
    yesBtn.onclick = async () => {
        const response = await fetch('/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(log)
        });
        const data = await response.json();
        if (data.suggestion) {
            recommendation.textContent = data.suggestion;
            recommendation.classList.remove('hidden');
            initialButtons.classList.add('hidden');
            fixButtons.classList.remove('hidden');
            // Store extracted code for fix
            fixBtn.dataset.code = data.extracted_code;
        } else {
            recommendation.textContent = `Error: ${data.error}`;
            recommendation.classList.remove('hidden');
        }
    };
    
    noBtn.onclick = () => {
        modal.classList.remove('show');
    };
    
    fixBtn.onclick = async () => {
        const response = await fetch('/apply-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ extracted_code: fixBtn.dataset.code })
        });
        const data = await response.json();
        if (data.status) {
            alert('Code change done successfully');
            modal.classList.remove('show');
        } else {
            alert(`Error: ${data.error}`);
        }
    };
    
    closeBtn.onclick = () => {
        modal.classList.remove('show');
    };
};