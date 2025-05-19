document.getElementById('run-connector').addEventListener('click', async () => {
    try {
        // Simulate realistic connector errors (30% chance each)
        const errorChance = Math.random();
        if (errorChance < 0.3) {
            // TypeError: Trying to call a method on undefined config
            const connectorConfig = undefined;
            connectorConfig.start(); // Causes TypeError
        } else if (errorChance < 0.6) {
            // ReferenceError: Undefined connector initialization function
            initializeConnector(); // Causes ReferenceError
        }
        // If no error, run connector
        const response = await fetch('/run-connector', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ connector: 'data-sync' })
        });
        const data = await response.json();
        console.log('Connector response:', data);
        if (data.status === 'success') {
            alert('Connector scheduled successfully!');
        }
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
    const suggestionInput = document.getElementById('suggestion-input');
    
    message.textContent = `Anomaly detected: ${log.message} (${log.error_type})`;
    recommendation.classList.add('hidden');
    recommendation.textContent = '';
    initialButtons.classList.remove('hidden');
    fixButtons.classList.add('hidden');
    suggestionInput.classList.add('hidden');
    modal.classList.add('show');
    console.log('Modal shown for anomaly:', log.message);

    // Handle Yes/No buttons
    const yesBtn = document.getElementById('suggest-yes');
    const noBtn = document.getElementById('suggest-no');
    const fixBtn = document.getElementById('fix-error');
    const closeBtn = document.getElementById('close-suggestion');
    const submitBtn = document.getElementById('submit-suggestion');
    
    yesBtn.onclick = () => {
        console.log('Yes button clicked');
        initialButtons.classList.add('hidden');
        suggestionInput.classList.remove('hidden');
        document.getElementById('user-suggestion').value = ''; // Clear previous input
    };
    
    submitBtn.onclick = async () => {
        console.log('Submit suggestion clicked');
        const userSuggestion = document.getElementById('user-suggestion').value;
        suggestionInput.classList.add('hidden');
        const response = await fetch('/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...log, user_suggestion: userSuggestion })
        });
        const data = await response.json();
        console.log('Suggest-fix response:', data);
        if (data.suggestion) {
            recommendation.textContent = data.suggestion;
            recommendation.classList.remove('hidden');
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
        suggestionInput.classList.add('hidden');
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
            suggestionInput.classList.add('hidden');
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
        suggestionInput.classList.add('hidden');
    };
};

// Debug SSE connection
source.onopen = () => console.log('SSE connection opened');
source.onerror = () => console.log('SSE connection error');