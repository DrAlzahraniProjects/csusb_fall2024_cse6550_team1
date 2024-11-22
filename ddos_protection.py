import time
import random
from collections import defaultdict
import streamlit as st

random.seed(1)

# Function to get the remote IP address
def get_remote_ip():
    # You can substitute this with a different method if you need to access headers directly, 
    # or use a proxy like NGINX that passes the client IP in a header.
    if st.session_state.current_user is None:
        st.session_state.current_user = random.randrange(0, 10000)
    return st.session_state.current_user  # Substitute this with actual IP fetching logic (like from request headers)

# Rate limit checker function
def is_rate_limited(user_ip):
    current_time = time.time()
    #requests = st.session_state.user_requests[user_ip]

    # Check if the user is in the lockout period
    if current_time < st.session_state.lockout_time[user_ip]:
        return True
    
    # Clean up the list to remove timestamps older than 1 minute
    st.session_state.user_requests[user_ip] = [ timestamp for timestamp in st.session_state.user_requests[user_ip] if current_time - timestamp < 60 ]
    # Debug: Check how many requests the user has made
    # st.write(f"Requests for {user_ip}: {len(st.session_state.user_requests[user_ip])}")
    # Check if the number of requests is over the limit
    if len(st.session_state.user_requests[user_ip]) >= 10:
        # Lock out the user for 3 minutes
        st.session_state.lockout_time[user_ip] = current_time + 180  # 3 minutes
        return True

    # If under the limit, allow the request
    return False

# Function to handle request rate limiting
def handle_rate_limiting():
    # Store user request information in session state
    user_ip = get_remote_ip()

    # Check if the user is rate-limited
    if is_rate_limited(user_ip):
        return False

    # If not rate-limited, allow the request and store the timestamp
    current_time = time.time()
    st.session_state.user_requests[user_ip].append(current_time)
    return user_ip
