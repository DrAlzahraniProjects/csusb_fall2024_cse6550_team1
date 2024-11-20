import time
import random
from collections import defaultdict
import streamlit as st
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()
random.seed(1)

# Store user request information in session state
if 'user_requests' not in st.session_state:
    st.session_state.user_requests = defaultdict(list)

# Function to get the remote IP address
def get_remote_ip():
    # You can substitute this with a different method if you need to access headers directly, 
    # or use a proxy like NGINX that passes the client IP in a header.
    if cookie_manager.get(cookie='user_id') is None:
        cookie_manager.set('user_id', random.randrange(0, 10000))
    return cookie_manager.get(cookie='user_id')  # Substitute this with actual IP fetching logic (like from request headers)

# Rate limit checker function
def is_rate_limited(user_ip):
    current_time = time.time()
    requests = st.session_state.user_requests[user_ip]

    # Clean up the list to remove timestamps older than 1 minute
    st.session_state.user_requests[user_ip] = [timestamp for timestamp in requests if current_time - timestamp < 60]

    # Debug: Check how many requests the user has made
    # st.write(f"Requests for {user_ip}: {len(st.session_state.user_requests[user_ip])}")

    # Check if the number of requests is over the limit
    if len(st.session_state.user_requests[user_ip]) >= 10:
        return True

    # If under the limit, allow the request
    return False

# Function to handle request rate limiting
def handle_rate_limiting():
    # Store user request information in session state
    if 'user_requests' not in st.session_state:
        st.session_state.user_requests = defaultdict(list)

    user_ip = get_remote_ip()

    # Check if the user is rate-limited
    if is_rate_limited(user_ip):
        st.error("You’ve reached the limit of 10 questions per minute because the server has limited resources. Please try again in 3 minutes.")
        st.stop()  # Stop further processing of the app

    # If not rate-limited, allow the request and store the timestamp
    current_time = time.time()
    st.session_state.user_requests[user_ip].append(current_time)
