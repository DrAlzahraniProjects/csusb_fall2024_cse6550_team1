# IT Support Chatbot

This repository contains the project for the IT Support Chatbot developed by the CSUSB Fall 2024 CSE6550 Team 1.

## Getting Started

Follow these instructions to set up the application locally using Docker.

### Prerequisites

Before you begin, make sure you have the following installed on your machine:

- [Docker](https://www.docker.com/get-started)
- [Git](https://git-scm.com/downloads)

### Installation

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

3. **Build the Docker image**

   Build the Docker image using the following command:

   ```bash
   docker build --no-cache -t itchatbot:latest .
   ```

4. **Run the Docker container**

   Run the Docker container with the following command:

   ```bash
   docker run -d -p 5001:5001 itchatbot
   ```

   The application will be accessible at: [http://localhost:5001](http://localhost:5001)

### Accessing the Application

Once the Docker container is running, you can access the IT Support Chatbot through your browser at:

[http://localhost:5001](http://localhost:5001)

---

### Troubleshooting

- If you encounter issues while building or running the container, ensure that Docker is installed and running correctly.
- Ensure the port `5001` is not being used by another application.

---

### Contributors

- CSUSB Fall 2024 CSE6550 Team 1

