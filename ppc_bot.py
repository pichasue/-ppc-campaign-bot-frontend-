import requests
import json
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import logging
import sqlite3

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

logging.info('Starting Flask server for PPC Campaign Management Bot')

# Constants for Amazon Advertising API
CLIENT_ID = 'your_amazon_client_id'
CLIENT_SECRET = 'your_amazon_client_secret'
PROFILE_ID = 'your_amazon_profile_id'
REFRESH_TOKEN = 'your_amazon_refresh_token'
REGION = 'na'  # Example region, change as needed
API_SCOPE = 'cpc_advertising:campaign_management'

# Amazon Advertising API URLs
TOKEN_URL = f'https://api.amazon.com/auth/o2/token'
BASE_URL = f'https://advertising-api.amazon.com'

# Constants for Facebook Marketing API
FB_APP_ID = 'your_facebook_app_id'
FB_APP_SECRET = 'your_facebook_app_secret'
FB_ACCESS_TOKEN = 'your_facebook_access_token'  # Long-lived token
FB_GRAPH_API_BASE_URL = 'https://graph.facebook.com/v19.0'

# Constants for Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN = 'your_google_ads_developer_token'
GOOGLE_ADS_CLIENT_ID = 'your_google_ads_client_id'
GOOGLE_ADS_CLIENT_SECRET = 'your_google_ads_client_secret'
GOOGLE_ADS_REFRESH_TOKEN = 'your_google_ads_refresh_token'
GOOGLE_ADS_CUSTOMER_ID = 'your_google_ads_customer_id'  # The 10-digit customer ID
GOOGLE_ADS_API_BASE_URL = 'https://googleads.googleapis.com/v9'

# Function to get access token for Amazon
def get_amazon_access_token():
    payload = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN
    }
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error getting Amazon access token: {response.text}")

# Function to get access token for Facebook
def get_facebook_access_token():
    # This function assumes that FB_ACCESS_TOKEN is already a long-lived token
    # If it's a short-lived token, implement the exchange process here
    return FB_ACCESS_TOKEN

# Function to get access token for Google Ads
def get_google_ads_access_token():
    url = 'https://accounts.google.com/o/oauth2/token'
    payload = {
        'client_id': GOOGLE_ADS_CLIENT_ID,
        'client_secret': GOOGLE_ADS_CLIENT_SECRET,
        'refresh_token': GOOGLE_ADS_REFRESH_TOKEN,
        'grant_type': 'refresh_token',
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'developerToken': GOOGLE_ADS_DEVELOPER_TOKEN,
        'login-customer-id': GOOGLE_ADS_CUSTOMER_ID
    }
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error getting Google Ads access token: {response.text}")

# Function to make a generic API call with retry mechanism and pagination
def make_api_call(endpoint, access_token, method='GET', data=None, params=None, platform='amazon'):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    if platform == 'amazon':
        headers['Amazon-Advertising-API-ClientId'] = CLIENT_ID
        headers['Amazon-Advertising-API-Scope'] = PROFILE_ID
        url = f'{BASE_URL}/{endpoint}'
    elif platform == 'facebook':
        url = f'{FB_GRAPH_API_BASE_URL}/{endpoint}'
    elif platform == 'google_ads':
        headers['developerToken'] = GOOGLE_ADS_DEVELOPER_TOKEN
        headers['login-customer-id'] = GOOGLE_ADS_CUSTOMER_ID
        url = f'{GOOGLE_ADS_API_BASE_URL}/{endpoint}'
    else:
        raise ValueError('Unsupported platform')

    attempt = 0
    max_attempts = 5
    backoff_factor = 2

    while attempt < max_attempts:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError('Unsupported method')

        if response.status_code == 200:
            # Handle pagination if 'nextToken' or 'paging' is present in the response
            response_data = response.json()
            if 'nextToken' in response_data:  # Amazon specific
                next_token = response_data['nextToken']
                params = params if params else {}
                params['nextToken'] = next_token
                continue
            elif 'paging' in response_data and 'next' in response_data['paging']:  # Facebook specific
                next_page = response_data['paging']['next']
                url = next_page  # The full URL is provided by the API for the next page
                continue
            return response_data
        elif response.status_code == 401:
            # Handle token expiration or invalid token
            if platform == 'amazon':
                access_token = get_amazon_access_token()  # Refresh the Amazon access token
            elif platform == 'facebook':
                access_token = get_facebook_access_token()  # Refresh the Facebook access token
            elif platform == 'google_ads':
                access_token = get_google_ads_access_token()  # Refresh the Google Ads access token
            continue  # Retry the API call with the new token
        elif response.status_code == 429:
            # Handle rate limiting
            time.sleep((backoff_factor ** attempt) * 60)  # Exponential backoff
            attempt += 1
            continue
        else:
            raise Exception(f"Error in API call: {response.status_code} {response.text}")
        break  # If successful or a non-retryable error occurs, exit the loop

# Optimization algorithm to adjust bids and budgets based on performance metrics
def optimize_campaigns(campaign_data):
    # Calculate average metrics from campaign data to use as dynamic thresholds
    total_clicks = sum(campaign['clicks'] for campaign in campaign_data)
    total_impressions = sum(campaign['impressions'] for campaign in campaign_data)
    total_spend = sum(campaign['spend'] for campaign in campaign_data)
    total_sales = sum(campaign['sales'] for campaign in campaign_data)

    # Avoid division by zero
    average_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
    average_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    average_roas = (total_sales / total_spend) if total_spend > 0 else 0

    optimized_campaigns = []
    for campaign in campaign_data:
        # Ensure all necessary fields are present
        if 'clicks' in campaign and 'impressions' in campaign and 'spend' in campaign and 'sales' in campaign:
            # Calculate current metrics with error handling for division by zero
            current_ctr = campaign['clicks'] / campaign['impressions'] if campaign['impressions'] > 0 else 0
            current_cpc = campaign['spend'] / campaign['clicks'] if campaign['clicks'] > 0 else 0
            current_roas = campaign['sales'] / campaign['spend'] if campaign['spend'] > 0 else 0

            # Determine bid adjustments with a more nuanced logic
            bid_adjustment = 1.0
            if current_ctr < average_ctr:
                bid_adjustment += 0.1
            elif current_ctr > average_ctr:
                bid_adjustment -= 0.1

            if current_cpc > average_cpc:
                bid_adjustment -= 0.1
            elif current_cpc < average_cpc:
                bid_adjustment += 0.1

            if current_roas < average_roas:
                bid_adjustment += 0.2
            elif current_roas > average_roas:
                bid_adjustment -= 0.2

            # Apply bid adjustment
            campaign['bid'] = max(campaign['bid'] * bid_adjustment, 0.01)  # Ensure bid does not go below a minimum threshold
        else:
            # If necessary data is missing, log an error or take appropriate action
            print(f"Missing data for campaign optimization: {campaign['campaignId']}")

        optimized_campaigns.append(campaign)

    return optimized_campaigns

app = Flask(__name__)
CORS(app)

@app.route('/api/login', methods=['POST'])
def login():
    # Predefined user credentials for demonstration purposes
    users = {
        'user@example.com': 'password123'
    }

    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if the email exists and the password matches
    if email in users and users[email] == password:
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    # Simulated campaign creation logic
    data = request.json
    campaign_name = data.get('campaignName')
    budget = data.get('budget')
    platform = data.get('platform')

    # Simulate campaign creation by generating a unique campaign ID
    campaign_id = f"{platform}_{int(time.time())}"

    # Log the campaign creation attempt with detailed information
    logging.info(f"Campaign creation attempt with data: {data}")

    # Return a success response with the simulated campaign ID
    return jsonify({'message': 'Campaign created successfully', 'campaignId': campaign_id}), 200

@app.route('/api/optimize', methods=['POST'])
def optimize_settings():
    # Receive optimization settings from the frontend
    data = request.json

    # Log the optimization settings received with detailed information
    logging.info(f"Optimization settings received: {data}")

    # Simulate applying optimization settings to campaigns
    # In a real scenario, this would involve complex logic and API calls
    # For now, we just log the settings and return a success message
    return jsonify({'message': 'Optimization settings applied successfully'}), 200

@app.route('/api/log', methods=['POST'])
def log_user_action():
    data = request.json
    action = data.get('action')
    status = data.get('status')
    timestamp = data.get('timestamp')

    # Log the user action with detailed information
    logging.info(f"User action logged: {action}, Status: {status}, Timestamp: {timestamp}")

    return jsonify({'message': 'User action logged successfully'}), 200

@app.route('/api/feedback', methods=['POST'])
def receive_feedback():
    # Access form data
    feedback_name = request.form['name']
    feedback_email = request.form['email']
    feedback_message = request.form['feedback']

    # Removed user_id as it's not provided by the form and updated the database insertion query
    try:
        # Establish a new database connection for each request
        with sqlite3.connect('ppc_bot.db') as conn:
            c = conn.cursor()
            # Insert the feedback into the database
            c.execute("INSERT INTO feedback (name, email, message, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (feedback_name, feedback_email, feedback_message))
            # Commit the changes
            conn.commit()
    except sqlite3.Error as e:
        # Log the exception and return an error response
        logging.error(f"Database error: {e}")
        return jsonify({'error': 'Failed to submit feedback'}), 500
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()

    # Log the feedback message with detailed information
    logging.info(f"Feedback received: {feedback_message}")

    return jsonify({'message': 'Feedback received successfully'}), 200

@app.route('/faq_content.md')
def faq_content():
    return send_from_directory('.', 'faq_content.md')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/dashboard')
def dashboard():
    logging.info('Dashboard route accessed')
    # Render the dashboard template with the necessary data
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
