// Main JavaScript file for handling form submissions and backend communication

// Function to handle the login form submission
function handleLogin(event) {
    event.preventDefault();
    // Retrieve login details from form
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    // AJAX call to backend for login
    fetch('http://127.0.0.1:5000/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Login failed');
        }
        return response.json();
    })
    .then(data => {
        console.log('Login successful:', data);
        // Handle login success, update UI or redirect as needed
        document.getElementById('loginError').textContent = '';
        // Log user action for successful login
        logUserAction('login', 'success');
    })
    .catch(error => {
        console.error('Login failed:', error);
        // Handle login failure, show error message to user
        document.getElementById('loginError').textContent = 'Invalid credentials. Please try again.';
        // Log user action for failed login
        logUserAction('login', 'failure');
    });
}

// Function to handle the campaign form submission
function handleCampaignForm(event) {
    event.preventDefault();
    // Retrieve campaign details from form
    const campaignName = document.getElementById('campaignName').value;
    const budget = document.getElementById('budget').value;
    const platform = document.getElementById('platform').value;
    // AJAX call to backend for campaign management
    fetch('http://127.0.0.1:5000/api/campaigns', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ campaignName, budget, platform })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Campaign creation failed');
        }
        return response.json();
    })
    .then(data => {
        console.log('Full response data:', data); // Added log for full response data
        console.log('Campaign created:', data);
        // Handle campaign creation success, update UI with campaign details
        document.getElementById('campaignCreationSuccess').textContent = `Campaign created successfully. Campaign ID: ${data.campaignId}`;
        // Log user action for successful campaign creation
        logUserAction('campaign_creation', 'success');
    })
    .catch(error => {
        console.error('Campaign creation failed:', error);
        // Handle campaign creation failure, show error message to user
        document.getElementById('campaignCreationSuccess').textContent = 'Failed to create campaign. Please try again.';
        // Log user action for failed campaign creation
        logUserAction('campaign_creation', 'failure');
    });
}

// Function to handle the optimization settings form submission
function handleOptimizationForm(event) {
    event.preventDefault();
    // Retrieve optimization settings from form
    const targetCPC = document.getElementById('targetCPC').value;
    const targetCPM = document.getElementById('targetCPM').value;
    const targetROAS = document.getElementById('targetROAS').value;
    // AJAX call to backend for optimization settings
    fetch('http://127.0.0.1:5000/api/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ targetCPC, targetCPM, targetROAS })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Optimization settings updated:', data);
        // Handle optimization success, update UI with optimization results
        // Log user action for successful optimization settings update
        logUserAction('optimization_settings', 'success');
    })
    .catch(error => {
        console.error('Optimization update failed:', error);
        // Handle optimization failure, show error message to user
        // Log user action for failed optimization settings update
        logUserAction('optimization_settings', 'failure');
    });
}

// Function to handle the feedback form submission
function handleFeedbackForm(event) {
    event.preventDefault();
    // Retrieve feedback message from form
    const feedbackMessage = document.getElementById('feedbackMessage').value;
    // AJAX call to backend for submitting feedback
    fetch('http://127.0.0.1:5000/api/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ feedbackMessage })
    })
    .then(data => {
        console.log('Feedback submitted:', data);
        // Handle feedback submission success, update UI with success message
        document.getElementById('feedbackSuccess').textContent = 'Thank you for your feedback!';
        document.getElementById('feedbackError').textContent = ''; // Clear any previous error message
        // Clear the feedback form
        document.getElementById('feedbackForm').reset();
    })
    .catch(error => {
        console.error('Feedback submission failed:', error);
        // Handle feedback submission failure, show error message to user
        document.getElementById('feedbackSuccess').textContent = ''; // Clear any previous success message
        document.getElementById('feedbackError').textContent = 'Failed to submit feedback. Please try again.';
    });
}

// Function to log user actions
function logUserAction(action, status) {
    // Log the user action to the backend for monitoring
    fetch('http://127.0.0.1:5000/api/log', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, status, timestamp: new Date().toISOString() })
    })
    .then(response => {
        if (!response.ok) {
            console.error('Failed to log user action:', action, status);
        }
    })
    .catch(error => {
        console.error('Error logging user action:', error);
    });
}

// Event listener for the feedback form submission
document.getElementById('feedbackForm').addEventListener('submit', handleFeedbackForm);

// Existing event listeners for form submissions
document.getElementById('loginForm').addEventListener('submit', handleLogin);
document.getElementById('campaignForm').addEventListener('submit', handleCampaignForm);
document.getElementById('optimizationForm').addEventListener('submit', handleOptimizationForm);

// Event listener for the create campaign button
document.getElementById('createCampaign').addEventListener('click', handleCampaignForm);
