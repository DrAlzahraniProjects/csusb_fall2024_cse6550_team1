# Basic StreamLit Docker Setup

Clone repository from HTTPS

```bash
$ git clone https://github.com/DrAlzahraniProjects/csusb_fall2024_cse6550_team1.git
```

Navigate to folder for repository

```bash
$ cd csusb_fall2024_cse6550_team1
```

Build the image using the following command

```bash
$ docker build --no-cache -t hello-world:latest .
```

Run the Docker container using the command shown below.

```bash
$ docker run -d -p 5001:5001 hello-world
```

The application will be accessible at http:127.0.0.1:5001 or http:localhost:5001