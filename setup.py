import os
import subprocess
import sys
import time
import shutil

def run_command(command, error_message):
    """Run a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e}")
        sys.exit(1)


def stop_and_remove_containers(ports):
    """Stop and remove Docker containers running on specific ports."""
    print("Stopping and removing Docker containers on ports:", ports)
    for port in ports:
        try:
            # Find the container ID using the port
            result = subprocess.check_output(f"docker ps -q -f publish={port}", shell=True).decode().strip()
            if result:
                print(f"Stopping container on port {port}...")
                run_command(f"docker stop {result}", f"Failed to stop container on port {port}")
                print(f"Removing container on port {port}...")
                run_command(f"docker rm {result}", f"Failed to remove container on port {port}")
            else:
                print(f"No container found running on port {port}.")
        except subprocess.CalledProcessError as e:
            print(f"Error while checking containers on port {port}: {e}")
            sys.exit(1)


def build_docker_image(groq_key):
    """Build the Docker image."""
    print("Building the Docker image...")
    run_command(f"docker build -t team1_app:latest . --build-arg GROQ={groq_key}", "Failed to build Docker image")


def display_loading_bar(duration):
    """Display a loading bar with time countdown for a specified duration."""
    print("Waiting for the application to fully load...")

    # Get terminal width for a dynamic progress bar
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    bar_width = min(50, terminal_width - 20)  # Adjust bar width dynamically

    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        progress = elapsed / duration
        completed = int(progress * bar_width)
        remaining = bar_width - completed
        time_left = duration - int(elapsed)

        # Build the loading bar
        bar = f"[{'#' * completed}{'.' * remaining}]"
        print(f"\r{bar} {int(progress * 100)}% | {time_left}s remaining", end="")
        time.sleep(0.1)  # Update every 100ms

    # Final clear and print
    print(f"\r{' ' * (bar_width + 30)}", end="\r")  # Clear the line
    print(f"[{'#' * bar_width}] 100% | 0s remaining")
    print("Application should now be ready!")


def run_docker_container():
    """Run the Docker container."""
    print("Running the Docker container...")
    run_command("docker run -d -p 5001:5001 -p 6001:6001 team1_app:latest", "Failed to run Docker container")
    print("Docker container started successfully!")
    display_loading_bar(30)  # 30 seconds duration
    print("You can now access the application:")
    print("Website: http://localhost:5001/team1")
    print("Wait 30 seconds more when accessing the webserver.")  # Additional message


def main():
    print("Starting cross-platform automation script.....")

    # Step 1: Stop and remove existing Docker containers
    ports = [5001]
    stop_and_remove_containers(ports)

    # Step 2: Build the Docker image
    groq_key = input("Enter your GROQ API key: ")
    build_docker_image(groq_key)

    # Step 3: Run the Docker container
    run_docker_container()


if __name__ == "__main__":
    main()