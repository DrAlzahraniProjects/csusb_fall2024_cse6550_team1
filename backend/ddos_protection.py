import time
import random
import json
import os
import streamlit as st
import requests
from collections import defaultdict

# Set the path for the JSON file to persist the rate-limiting data
JSON_FILE_PATH = 'user_rate_limit_data.json'

# Initialize random seed for randomness
random.seed(1)

# Function to load data from JSON file into session state
def load_data():
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as f:
            data = json.load(f)
            user_requests = data.get('user_requests', {})
            lockout_time = data.get('lockout_time', {})
    else:
        user_requests = {}
        lockout_time = {}

    # Store loaded data in session state for easy access
    st.session_state.user_requests = defaultdict(list, user_requests)
    st.session_state.lockout_time = lockout_time

# Function to get the remote IP address (can be from headers or external service)
def get_remote_ip():
    """
    Function to get the remote IP address of the user from the request headers
    or an external service like ipify if behind a proxy.
    """
    if 'X-Real-IP' in st.query_params:
        user_ip = st.query_params['X-Real-IP'][0]
    elif 'X-Forwarded-For' in st.query_params:
        user_ip = st.query_params['X-Forwarded-For'][0].split(',')[0]
    else:
        # If no IP found in headers, use an external service (ipify)
        response = requests.get('https://api.ipify.org')
        user_ip = response.text

    return user_ip

# Rate limit checker function
def is_rate_limited(user_ip):
    """
    Function to check if the user is rate-limited.

    Args:
        user_ip (str): The IP address of the user.

    Returns:
        bool: True if the user is rate-limited, False otherwise.
    """
    current_time = time.time()

    # Check if the user is in the lockout period
    lockout_time_user = st.session_state.lockout_time.get(user_ip, 0)
    if current_time < lockout_time_user:
        return True

    # Clean up the list to remove timestamps older than 1 minute
    st.session_state.user_requests[user_ip] = [
        timestamp for timestamp in st.session_state.user_requests[user_ip]
        if current_time - timestamp < 60
    ]

    # Check if the number of requests is over the limit
    if len(st.session_state.user_requests[user_ip]) >= 10:
        # Lock out the user for 3 minutes
        st.session_state.lockout_time[user_ip] = current_time + 180  # 3 minutes lockout
        
        # Save data to JSON after the lockout time is set
        save_data_to_json()
        return True

    return False

# Function to handle rate-limiting
def handle_rate_limiting():
    """
    Function to handle rate-limiting for the user.

    Returns:
    str or bool: The user IP if the request is allowed, False if the request is rate-limited.
    """
    user_ip = get_remote_ip()
    load_data()

    # Check if the user is rate-limited
    if is_rate_limited(user_ip):
        return False

    # If not rate-limited, allow the request and store the timestamp
    current_time = time.time()
    st.session_state.user_requests[user_ip].append(current_time)

    # Save updated data to the JSON file
    save_data_to_json()

    return user_ip

# Function to save the data to a JSON file
def save_data_to_json():
    """
    Save the user requests and lockout time to a JSON file for persistence.
    """
    data = {
        'user_requests': {user_ip: timestamps for user_ip, timestamps in st.session_state.user_requests.items()},
        'lockout_time': st.session_state.lockout_time
    }

    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)