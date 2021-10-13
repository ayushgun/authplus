# auth-plus 

<img src="https://github.com/ayushgun/auth-plus/blob/main/images/main.png" alt="Logo" width="400">

Auth Plus is a Python-based MongoDB and Flask API that allows for username, password, and HWID authentication.

![GitHub last commit](https://img.shields.io/github/last-commit/ayushgun/auth-plus?logo=github) ![GitHub repo size](https://img.shields.io/github/repo-size/ayushgun/auth-plus?logo=github)

Auth Plus is highly customizable and modifiable. Although there is no official documentation, each Flask function includes docstrings that explain the purpose, intent, and access level of the endpoint. 

- [auth-plus](https://authpl.us)
  - [Quick Start](#quick-start)
  - [Important Notes](#important)
  - [Credits](#credits)
  - [LICENSE](https://github.com/ayushgun/auth-plus/blob/main/LICENSE)

# Quick Start
Ready to locally host the API?

1. Create two MongoDB Atlas Clusters. One must hold user:pass:HWID information while the other must hold license information. This [video](https://www.youtube.com/watch?v=rE_bJl2GAY8) created by "Tech with Tim" explains how to construct the Cluster Database.

2. Adjust the URIs, database names, and collection names located under `# USER DB CONFIG` and `# LICENSE DB CONFIG` in **main.py**

3. Parse code and adjust endpoints as nessecary

4. Adjust the client and admin passwords located in **roles.txt**

5. Assuming Python and Pip are pre-installed, run `pip install -r requirements.txt`

6. Run `python main.py` to start the API

# Todo
In the near future, I will be adding a sample client application that works with the AuthPlus API

# Important
Please note that the API will NOT start without adjusting the config correctly. Please carefully follow the "Tech with Tim" [video](https://www.youtube.com/watch?v=rE_bJl2GAY8) linked to understand how to set up a MongoDB cluster properly. Additionally, please note that the PyMongo setup displayed in the Tech with Tim video is not nessecary, though it may be beneficial to conceptually understand the API.

# Credits
Thank you to Tech with Tim for his amazing MongoDB and PyMongo tutorial

Thank you to Flask for their incredible documentation.
