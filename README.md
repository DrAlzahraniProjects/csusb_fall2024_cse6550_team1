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

3. **Update the local repository**

   Ensure your local repository is up to date by running:

   ```bash
   git pull origin main
   ```
   
4. **Build the Docker image**

   Build the Docker image using the following command:

   *DO NOT RUN THIS COMMAND YET, THE API KEY IN STEP 5 MUST BE INCLUDED AT THE END OF THE COMMAND*

   ```bash
   docker build -t team1_app:latest . --build-arg MISTRAL=
   ```

5. **Include the API key**

   - Go to [Team1 QA](https://csusb.instructure.com/courses/43192/discussion_topics/419701) and copy the MISTRAL API key
   - Paste the API key at the end of the previous instruction
   - Your command should look like this:
   ```bash
   docker build -t team1_app:latest . --build-arg MISTRAL=APIKEYHERE
   ```
   - Run the command

6. **Run the Docker container**

   ### Windows PS or Docker Desktop Terminal

   Run the Docker container with the following command:

   ```bash
   docker run -v $pwd/milvus:/app/milvus -v $pwd/logs:/app/logs -d -p 5001:5001 -p 6001:6001 team1_app
   ```

   ### Windows CMD
   
   Run the Docker container with the following command:

   ```bash
   docker run -v %cd%/milvus:/app/milvus -v %cd%/logs:/app/logs -d -p 5001:5001 -p 6001:6001 team1_app
   ```

   ### Linux CLI
   
   Run the Docker container with the following command:

   ```bash
   docker run -v $PWD/milvus:/app/milvus -v $PWD/logs:/app/logs -d -p 5001:5001 -p 6001:6001 team1_app
   ```

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


| **Answerable**                                      | **Unanswerable**                                 |
|-----------------------------------------------------|--------------------------------------------------|
| How can I contact ITS?                              | How do I connect to Starbucks Wi-Fi?             |
| How can I connect to the campus Wi-Fi?              | What is a smart contract?                        |
| Who are the Co-Chairs for the 2024/2025 Committee?  | Can you write code for a basic Python script?     |
| Where are all the printers located?                 | Who is the dean of CSUSB?                        |
| What are the CoyoteLabs virtual computer lab?       | What class does Dr. Alzahrani teach?             |
| Is Adobe Creative Cloud available as student software? | Who is Hironori Washizaki?                    |
| Does CSUSB have accessible technology?              | When was CSUSB built?                            |
| How do I enable multi-factor authorization?         | What is the future impact of AI on software quality standards? |
| What are Coyote OneCard benefits?                   | What is regression testing?                     |
| Why can't I get access for wireless prints through phone? | Can a student apply a part-time job in IT support if so what is the process? |


## Troubleshooting

- If you encounter issues while building or running the container, ensure that Docker is installed and running correctly.
- Ensure the port `5001` is not being used by another application.

---

## Contributors

- CSUSB Fall 2024 CSE6550 Team 1

