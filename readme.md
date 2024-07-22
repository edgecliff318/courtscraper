# README #

Version : 0.0.2

# **Overview**

Fubloo App provides a user friendly interface for **Leads Monitoring**. From construction to results display, everything can be handled from the dashboard.

The dashboard was developed using **python 3.8.8**.

---

# **How do I run the dashboard?**

Using a python interpreter (version 3.8.8) you can run the dashboard by running `server.py` file. Make sure to install the project dependencies referenced in requirement.txt `pip install -r requirements.txt`.


```
python server.py
```

---

# **Architecture**

## **Components**

Each tab has its own module within the tabs module. Whenever you insert a new tab make sure to add it to tabs/**init****.py. This way when importing `components.tabs` it will import all the tabs available in the project.

### **tabs**

→ Defines the content for each tab of the dashboard.

**figures.py** → Displays on the dashboard the results calculated in core.py.

**markdown.py** → Markdown is a Python library that allows you to convert Markdown text to HTML. markdown.py include the texts needed for the dashboard.

**tables.py** → Provides formatting function to display serie on the dashboard. Also includes formatting function to display key periods.

### **Core**

→ The core modules contains the main modules used for the calculations in the dashboard

## **Data**

## **loader**
→ Handle the loading of data

## **temp**

→ Cached objects saved in a binary format with the module [pickle](https://docs.python.org/3/library/pickle.html).

**callbacks.py** → Regroup callback functions.

**gunicorn_config.py** → Python WSGI HTTP. (for production)

**setup.py** → Description générique du module (non utilisé ici)

# **Contribution guide**

→ Below is a tutorial for contributing to the dashboard, covering our tools and typical process.

→ Refer to the roadmap (on [Jira Software](https://neoinvest.atlassian.net/)) for a list of user stories the project could really benefit from. In addition, the following is always welcome:

- Improve performance of existing code (but not at the cost of readability).
- Improve coverage by writing some more tests.
- Improve user experience/interface and readability.

## **Seek early feedback**

Before you start coding your contribution, it may be wise to raise an issue/user story on J[ira Software](https://neoinvest.atlassian.net/) to discuss whether the contribution and its architecture.

## **Get started**

1. Download :
    - PyCharm or Visual Studio
    - Github
2. Clone the repository **app** to your machine from Github
3. Open Pycharm and select open then select the folder where you have cloned the repository
4. Modify the project preferences of PyCharm as follow where you will setup a new virtual python environment(the importance is [explained here](https://towardsdatascience.com/getting-started-with-python-environments-using-conda-32e9f2779307) of having a separate environment for each project)

## **Clone the repository**

Use these steps to clone from SourceTree, our client for using the repository command-line free. Cloning allows you to work on your files locally. If you don't yet have SourceTree, [download and install first](https://www.sourcetreeapp.com/). If you prefer to clone from the command line, see [Clone a repository](https://confluence.atlassian.com/x/4whODQ).

1. You’ll see the clone button under the **Source** heading. Click that button.
2. Now click **Check out in SourceTree**. You may need to create a SourceTree account or log in.
3. When you see the **Clone New** dialog in SourceTree, update the destination path and name if you’d like to and then click **Clone**.
4. Open the directory you just created to see your repository’s files.

## **Developments Requirements**

After setting the environment for the project, you need to install the requirements:

```
pip install -r requirements.txt
```

Additional requirements for developments can be installed using:

```
pip install -r requiremnets_dev.txt
```

## **Adding unitary tests to your code**

Unitary tests are important to ensure an optimal code coverage when adding new functionalities or correcting existing one. Some can argue that they are as important as the code itself and some design patterns suggest creating the test case before starting to dig how to code a functionality. You can inspire yourself from the existing test code present within the project repository.

→ You can run your file test using **Unittests**  or **Nosetests** to see the tests results.

Note: It is best to associate a test script (`test_*.py`) with each python script.

## Test coverage

Test coverage is a measure used to describe the degree to which the source code of the project is executed when a particular test suite runs.

To test the full project, you can use the following shell command :

```
nosetests --with-coverage
```

To display a report you can use the following command :

```bash
coverage report

#or

coverage html
```

→ `coverage html` generate an html detailed report. You can access it from **index.html** in **htmlcov**.

## **Debug an issue**

1. Set your breakpoints next to the code you would like to debug.
2. Run **Debug** on your .py script.

Note: Details on how to use pycharm's debugger can be found in PyCharm [documentation](https://www.jetbrains.com/help/pycharm/debugging-your-first-python-application.html).

When validating a functionality and debugging, it's better to use the test functions.

## **Documentation**

Inline comments and docstrings are great when needed, but don't overload the them. Docstrings should follow [PEP257](https://stackoverflow.com/questions/2557110/what-to-put-in-a-python-module-docstring) semantically and syntactically.

Accompany the changes with relevant documentation. Make it simple and as complete as possible.

## **Commit your code**

1. Using Sourcetree, open your local repository and select a branch.
2. Press the commit button.
3. Review and select the files that you have edited to Commit.
4. Name the Commit after the associated user story from [Jira Software](https://neoinvest.atlassian.net/) and/or add meaningful messages (the issue / feature id from bitbucket). At the beginning of the commit message, put the issue id from JIRA (e.g ROAD-504 New dashboard widget for historical returns)

Note: Ensure that you have sufficient test coverage on your code before you commit any code.

## Setting up the application locally

- Install chromium
`brew install chromium`
- Update Chrome to the latest version
- Install Selenium
`pip install selenium`
- Install poppler for PDF transformation
`brew install poppler`

# **License**

© All rights reserved, [Fubloo](https://fubloo.com/), Ayoub Ennassiri, [ayoub.ennassiri@neoinvest.ai](mailto:ayoub.ennassiri@neoinvest.ai)

No part of this project may be used, published or shared under any circumstances unless expressly requested by the rights holder of this document.

By contributing, you agree that your contributions will be fully accredited to [Fubloo](https://fubloo.com/). (Refer to the upper copyright statement)
