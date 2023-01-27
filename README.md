<h1 align="center">
  <img src="assets/logo.png" width="400px">
  <br>
  AuthPlus
</h1>
<p align="center">
  <img src="https://img.shields.io/github/deployments/ayushgun/authplus/github-pages?label=build&logo=github&style=flat-square"/>
  <a href="https://github.com/ayushgun/authplus/releases/latest">
    <img src="https://img.shields.io/github/v/tag/ayushgun/authplus?label=version&style=flat-square"/>
  </a>
  <a href="LICENSE.md">
    <img src="https://img.shields.io/github/license/ayushgun/authplus?style=flat-square"/>
  </a>
</p>

# Overview

AuthPlus is lightweight, scalable, and secure hardware-based user authentication API.

AuthPlus makes it easy for developers to restrict their applications to specific target machines.

AuthPlus features:

- User authentication and management
- License generation and management
- Out of the box parameter validation
- HMAC (SHA256) response data encryption
- Built-in request ratelimiting

AuthPlus is built to be self-hosted and configured to users needs.

# Getting Started

Ready to self-host AuthPlus?

1. Ensure that [Go](https://go.dev/dl/) and [Python](https://www.python.org/downloads/) are installed on the machine.

2. Clone the repository with `git clone https://github.com/ayushgun/authplus`.

3. Initialize a MongoDB cluster with a database titled `authentication` and two collections titled `licenses` and `users`. Set the `database_uri` in `configuration/config.env` to the MongoDB connection URI.

4. Generate a Fernet encryption key using this [script](https://gist.github.com/ayushgun/1fd456f8cfb51e1d6ccf21d52c39317f). Set the `encryption_key` in `configuration/config.env` to the generated Fernet encryption key.

5. Set the `admin_password` and `client_password` in `configuration/config.env` to two randomly generated passwords. These passwords are used for HTTP basic authentication, and should be scoped to the client and server level.

6. Customize the API URL and port by setting `api_url` in `configuration/config.env` to the desired `port:url`. A default localhost URL has been set out of the box.

7. Run the API with `go run main.go`. All API dependencies will automatically be installed, given that Go is locally installed and set up correctly.

# Testing

If you plan on modifying the API, a default test suite has been included in this repository.

To run the test suite:

1. Ensure that [pip](https://pypi.org/project/pip/) is installed on the machine.

2. Start the API with `go run main.go`.

3. Move to the test suite directory with `cd tests`. Then, install the test suite dependencies with `pip3 install -r requirements.txt`.

4. Run the test suite with `python3 api_tests.py`.

# Contributing

We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting an issue
- Discussing the current state of the project
- Submitting a fix
- Proposing new features

To get started, check [Issues](https://github.com/ayushgun/authplus/issues) for a list of tracked issues.

# Acknowledgements

[Ayush Gundawar](https://github.com/ayushgun) is the author of this project. His website can be found [here](https://ayushgundawar.me).

[Gin](https://github.com/gin-gonic/gin) is the foundational technology used to build AuthPlus. Thank you to the open-source Gin community for building a wonderful, lightweight, and performant HTTP web framework.
