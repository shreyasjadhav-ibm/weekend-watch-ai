document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    try {
        // Simulate JS error randomly
        if (Math.random() < 0.2) {
            // Removed the call to the undefined function
        }
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        console.log('Login response:', data);
    } catch (error) {
        console.log('Error caught:', error.message, error.name);
        const logResponse = await fetch('/log-error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: 'frontend',
                message: error.message,
                error_type: error.name
            })
        });
        console.log('Log error response:', await logResponse.json());
    }
});

// Intentional syntax error for testing - corrected
function brokenSyntax() {
    console.log("This is broken");
}

// Initialize modal as hidden
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('alert-modal');
    modal.classList.remove('show');
    console.log('Modal initialized: hidden');
});

// SSE for anomaly alerts
const source = new EventSource('/alerts');
source.onmessage = function(event) {
    console.log('SSE message received:', event.data);
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
    console.log('Modal shown for anomaly:', log.message);

    // Handle Yes/No buttons
    const yesBtn = document.getElementById('suggest-yes');
    const noBtn = document.getElementById('suggest-no');
    const fixBtn = document.getElementById('fix-error');
    const closeBtn = document.getElementById('close-suggestion');
    
    yesBtn.onclick = async () => {
        console.log('Yes button clicked');
        const response = await fetch('/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(log)
        });
        const data = await response.json();
        console.log('Suggest-fix response:', data);
        if (data.suggestion) {
            recommendation.textContent = data.suggestion;
            recommendation.classList.remove('hidden');
            initialButtons.classList.add('hidden');
            fixButtons.classList.remove('hidden');
            fixBtn.dataset.code = data.extracted_code;
        } else {
            recommendation.textContent = `Error: ${data.error}`;
            recommendation.classList.remove('hidden');
        }
    };
    
    noBtn.onclick = () => {
        console.log('No button clicked');
        modal.classList.remove('show');
        recommendation.classList.add('hidden');
        initialButtons.classList.remove('hidden');
        fixButtons.classList.add('hidden');
    };
    
    fixBtn.onclick = async () => {
        console.log('Fix button clicked');
        const response = await fetch('/apply-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ extracted_code: fixBtn.dataset.code })
        });
        const data = await response.json();
        console.log('Apply-fix response:', data);
        if (data.status) {
            alert('Code change done successfully');
            modal.classList.remove('show');
            recommendation.classList.add('hidden');
            initialButtons.classList.remove('hidden');
            fixButtons.classList.add('hidden');
        } else {
            alert(`Error: ${data.error}`);
        }
    };
    
    closeBtn.onclick = () => {
        console.log('Close button clicked');
        modal.classList.remove('show');
        recommendation.classList.add('hidden');
        initialButtons.classList.remove('hidden');
        fixButtons.classList.add('hidden');
    };
};

// Debug SSE connection
source.onopen = () => console.log('SSE connection opened');
source.onerror = () => console.log('SSE connection error');