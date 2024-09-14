import streamlit as st
import os
import subprocess

def main():
	st.title("Hello World! - Team 1")

if __name__ == "__main__":
	# If streamlit instance is running
	if os.environ.get("STREAMLIT_RUNNING") == "1":
		main()

	# If streamlit is not running
	else:
		os.environ["STREAMLIT_RUNNING"] = "1" # Set the environment variable to indicate Streamlit is running
		subprocess.run(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0"])
