# IT Support Chatbot

This repository contains the IT Support Chatbot project developed by **CSUSB Fall 2024 CSE6550 Team 1**. The chatbot is designed to assist users with IT-related queries and support.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Accessing the Application](#accessing-the-application)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)

## Getting Started

Follow these instructions to set up the application locally using Docker.

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

- [Docker](https://www.docker.com/get-started)
- [Git](https://git-scm.com/downloads)

## Installation Guides

### Building and Running from Source Code

1. **Clone the repository**

   Clone the repository from the main branch:

   ```bash
   git clone -b main --single-branch https://github.com/DrAlzahraniProjects/csusb_fall2024_cse6550_team1.git
   ```

2. **Navigate to the project folder**

   Change your directory to the repository folder:

   ```bash
   cd csusb_fall2024_cse6550_team1
   ```

3. **Update the local repository**

   Ensure your local repository is up to date by running:

   ```bash
   git pull origin main
   ```
   
4. **Build the Docker image**

   Build the Docker image using the following command:

   ```bash
   docker build --build-arg MISTRAL=API_KEY_HERE -t team1_app:latest .
   ```

5. **Run the Docker container**

   Run the Docker container with the following command:

   ```bash
   docker run -d -p 5001:5001 -p 6001:6001 team1_app
   ```

### Accessing the Application

Once the Docker container is running, you can access the IT Support Chatbot through your browser at:

[http://localhost:5001/team1](http://localhost:5001/team1) or [http://127.0.0.1:5001/team1](http://127.0.0.1:5001/team1)

You can access the Jupyter Notebook at:

[http://localhost:6001/team1/jupyter](http://localhost:6001/team1/jupyter) or [http://127.0.0.1:6001/team1/jupyter](http://127.0.0.1:6001/team1/jupyter)

---

### Troubleshooting

- If you encounter issues while building or running the container, ensure that Docker is installed and running correctly.
- Ensure the port `5001` is not being used by another application.

---

### Contributors

- CSUSB Fall 2024 CSE6550 Team 1

