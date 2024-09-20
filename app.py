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
		subprocess.Popen(["streamlit", "run", __file__, "--server.port=5001", "--server.address=0.0.0.0"])
		subprocess.Popen(["service", "nginx", "start"])
		subprocess.run(["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"])
