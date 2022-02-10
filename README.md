# AuthPlus
<img src="https://github.com/ayushgun/auth-plus/blob/main/images/main.png" alt="Logo" width="400">

![GitHub last commit](https://img.shields.io/github/last-commit/ayushgun/auth-plus?logo=github) ![GitHub repo size](https://img.shields.io/github/repo-size/ayushgun/auth-plus?logo=github)

AuthPlus is an authentication solution built for the future. AuthPlus has been developed from the ground up with software developers and Web3 infrastructure in mind. 

At its core, AuthPlus is a Python-based Flask API that allows for hardware-level user authentication.

AuthPlus is highly customizable and scalable. The official documentation is located under each Flask method; these methods includes docstrings that explain the purpose, intent, and access level of the endpoint. 

- [AuthPlus](https://authpl.us)
  - [Quick Start](#quick-start)
  - [Important Notes](#important)
  - [LICENSE](https://github.com/ayushgun/auth-plus/blob/main/LICENSE)

# Quick Start
Ready to locally host the API?

1. Create two MongoDB Atlas Clusters. One must hold user:pass:HWID information while the other must hold license information. This [video](https://www.youtube.com/watch?v=rE_bJl2GAY8), created by Tim Ruscica, explains how to construct a MongoDB Cluster Database.

2. Adjust the URIs, database names, and collection names located under `# USER DB CONFIG` and `# LICENSE DB CONFIG` in `main.py`

3. Parse code and adjust endpoints as nessecary

4. Adjust the client and admin passwords located in `roles.txt` file

5. Assuming Python and the pip package manager are pre-installed, run `pip install -r requirements.txt`

6. Run `python main.py` to start the API

# AuthPlus V5
Thank you to everyone who has supported AuthPlus V4. The developer team is currently working on developing a redesigned version of AuthPlus with an emphasis on semantics, scalability, and documentation. AuthPlus V5 will be built with the FastAPI framework. 

✉️ Interested in contributing? Create a pull request and we'll review it!

# Important
Please note that the API will NOT start without adjusting the config correctly. Additionally, please note that the PyMongo setup displayed in Tim Ruscia's wonderful video is not nessecary, though it may be beneficial to conceptually understand the API.

# License
AuthPlus is officially licensed under the MIT license. It is a project meant for the public domain, and fully supports open source development.
