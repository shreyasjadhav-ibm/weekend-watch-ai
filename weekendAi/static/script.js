function initializeConnector() {
    console.log('Connector initialized (placeholder)');
    // Add your actual connector initialization logic here if needed.
}

document.getElementById('run-connector').addEventListener('click', async () => {
    try {
        // Simulate realistic connector errors 
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

// SSE for anomaly alerts (approvals hardcoded)
let currentIssueId = null;
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
    const waitingApproval = document.getElementById('waiting-approval');
    const loadingAnimation = document.getElementById('loading-animation');
    const fixBtn = document.getElementById('fix-error');

    // Only handle anomaly alerts (approvals hardcoded in submitBtn)
    message.textContent = `Anomaly detected: ${log.message} (${log.error_type})`;
    recommendation.classList.add('hidden');
    recommendation.textContent = '';
    initialButtons.classList.remove('hidden');
    fixButtons.classList.add('hidden');
    suggestionInput.classList.add('hidden');
    waitingApproval.classList.add('hidden');
    modal.classList.add('show');
    console.log('Modal shown for anomaly:', log.message);

    // Handle Yes/No buttons
    const yesBtn = document.getElementById('suggest-yes');
    const noBtn = document.getElementById('suggest-no');
    const closeBtn = document.getElementById('close-suggestion');
    const submitBtn = document.getElementById('submit-suggestion');
    
    yesBtn.onclick = () => {
        console.log('Yes button clicked');
        initialButtons.classList.add('hidden');
        suggestionInput.classList.remove('hidden');
        document.getElementById('user-suggestion').value = '';
    };
    
    submitBtn.onclick = async () => {
        console.log('Submit suggestion clicked');
        const userSuggestion = document.getElementById('user-suggestion').value;
        suggestionInput.classList.add('hidden');
        loadingAnimation.classList.add('show');
        const response = await fetch('/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...log, user_suggestion: userSuggestion })
        });
        loadingAnimation.classList.remove('show');
        const data = await response.json();
        console.log('Suggest-fix response:', data);
        if (data.suggestion) {
            currentIssueId = data.issue_id;
            recommendation.textContent = data.suggestion;
            recommendation.classList.remove('hidden');
            waitingApproval.classList.remove('hidden');
            waitingApproval.textContent = 'Waiting for developer approval...';
            fixButtons.classList.remove('hidden');
            fixBtn.dataset.code = data.extracted_code;
            fixBtn.dataset.issueId = data.issue_id;
            fixBtn.disabled = true;
            console.log(`Set currentIssueId: ${currentIssueId}`);
            // Hardcode approval: enable button after 10 seconds
            setTimeout(() => {
                waitingApproval.textContent = 'Developer has approved this change, try again in a minute';
                fixBtn.disabled = false;
                fixBtn.classList.remove('disabled');
                console.log(`Hardcoded approval for issue_id: ${currentIssueId}`);
            }, 10000); // 10 seconds
        } else {
            recommendation.textContent = `Error: ${data.error}`;
            recommendation.classList.remove('hidden');
            waitingApproval.classList.add('hidden');
        }
    };
    
    noBtn.onclick = () => {
        console.log('No button clicked');
        modal.classList.remove('show');
        recommendation.classList.add('hidden');
        initialButtons.classList.remove('hidden');
        fixButtons.classList.add('hidden');
        suggestionInput.classList.add('hidden');
        waitingApproval.classList.add('hidden');
        currentIssueId = null;
    };
    
    fixBtn.onclick = async () => {
        console.log('Fix button clicked');
        const response = await fetch('/apply-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                extracted_code: fixBtn.dataset.code,
                issue_id: fixBtn.dataset.issueId
            })
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
            waitingApproval.classList.add('hidden');
            currentIssueId = null;
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
        waitingApproval.classList.add('hidden');
        currentIssueId = null;
    };
};

// Debug SSE connection
source.onopen = () => console.log('SSE connection opened');
source.onerror = () => console.log('SSE connection error');