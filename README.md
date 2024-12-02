# IT Support Chatbot

This repository contains the IT Support Chatbot project developed by **CSUSB Fall 2024 CSE6550 Team 1**. The chatbot is designed to assist users with IT-related queries and support.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Accessing the Application](#accessing-the-application)
- [SQA for IT Chatbot](#software-quality-assurance-for-the-it-chatbot)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)

## Getting Started

Follow these instructions to set up the application locally using Docker.

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

- [Docker](https://www.docker.com/get-started)
- [Git](https://git-scm.com/downloads)

## Installation Guide

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
3. **Discard changes**

   Discard all local changes:
   ```bash
   git reset --hard
   ```

4. **Update the local repository**

   Ensure your local repository is up to date by running:

   ```bash
   git pull origin main
   ```
   
5. **Run the setup scrpit**

   Setup script that runs relevant Docker commands and prompts user for the API Key:
   ```bash
   python setup.py
   ```

   **Note**: If the above command does not work (e.g., on Linux), try using:

   ```bash
   python3 setup.py
   ```

6. **Follow On-Screen Prompts**

   - The script will ask for the GROQ API key that can be found [here](https://csusb.instructure.com/courses/43192/discussion_topics/419701)
   - It will stop any existing containers, pull updates, build the Docker image, and run the container

## Accessing the Application

### Accessing locally through Docker 
Once the Docker container is running, you can access the IT Support Chatbot through your browser at:

[http://localhost:5001/team1](http://localhost:5001/team1) or [http://127.0.0.1:5001/team1](http://127.0.0.1:5001/team1)

You can access the Jupyter Notebook at:

[http://localhost:6001/team1/jupyter](http://localhost:6001/team1/jupyter) or [http://127.0.0.1:6001/team1/jupyter](http://127.0.0.1:6001/team1/jupyter)

### Accessing through the CSE web server
Access through the CSE web server at:

[https://sec.cse.csusb.edu/team1](https://sec.cse.csusb.edu/team1)

You can access the Jupyter Notebook at:

[https://sec.cse.csusb.edu/team1/jupyter](https://sec.cse.csusb.edu/team1/jupyter)

## Software Quality Assurance for the IT Chatbot

This section highlights the sets of questions the chatbot can and cannot answer.


| **Answerable**                                         | **Unanswerable**                                               |
|--------------------------------------------------------|----------------------------------------------------------------|
| How can I contact ITS?                                 | What are the campus gym timings?                               |
| How can I connect to the campus Wi-Fi?                 | What is a smart contract?                                      |
| What are the available free software for a student?    | Can you write code for a basic Python script?                  |
| Where are all the printers located?                    | What is the CGI phone number/email?                            |
| What are the CoyoteLabs virtual computer labs?         | What class does Dr. Alzahrani teach?                           |
| Is Adobe Creative Cloud available as student software? | Who is Hironori Washizaki?                                     |
| What is information security awareness?                | How can I make a payment for the tuition fee?                  |
| How do I enable multi-factor authentication?           | What is the future impact of AI on software quality standards? |
| What are Coyote OneCard benefits?                      | What is regression testing?                                    |
| What if i lost my campus laptop charger?               | How much does parking cost for one semester?                   |


## Troubleshooting

- If you encounter issues while building or running the container, ensure that Docker is installed and running correctly.
- Ensure the port `5001` is not being used by another application.

---

## Contributors

- CSUSB Fall 2024 CSE6550 Team 1

