

import setuptools



"""Read and return requirements from 'requirements.txt'."""
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()



def read_long_description():
    """Read and return the long description from 'README.md'."""
    with open("README.md", "r") as file:
        return file.read()


# Variables
PACKAGES = setuptools.find_packages(
    where=".",
    exclude=["tests", "tests.*", "test", "test.*"],
)

INSTALL_REQUIRES = [
     "dash>=2.5.0",
    "dash[diskcache]",
    "dash-bootstrap-components>=1.1.0",
    "dash-ag-grid>=2.2.0",
    "dash-iconify",
    "dash-mantine-components",
    "gunicorn>=20.1.0",
    "werkzeug>=2.1.2",
    "PyJWT>=2.3.0",
    "authlib>=1.0",
    "pydantic",
    "pydantic_settings",
    "requests>=2.26.0",
    "flask_cors>=3.0.10",
    "typer>=0.4.0",
    "rich>=12.5.1",
    "pandas>=1.3.5",
    "gcloud>=0.18.3",
    "google-cloud-vision>=2.6.3",
    "commonregex",
    "beautifulsoup4>=4.10.0",
    "pdf2image>=1.16.0",
    "docxtpl>=0.15.2",  # Fixed typo (removed "ù" at the end)
    "unidecode>=1.3.4",
    "twilio",
    "pillow",
    "pypdf",
    "firebase-admin",
    "google-api-python-client",
    "google-auth-httplib2",
    "google-auth-oauthlib",
    # "langchain",
    "openai",
    "stripe"
]

setuptools.setup(
    name="fubloo",
    version="0.0.1",
    author="Neoinvest.ai",
    author_email="ayoub.ennassiri@neoinvest.ai",
    description="This package contains various helpers for devs",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    packages=PACKAGES,
    include_package_data=True,
    exclude_package_data={
        "": ["tests", "tests.*", "test.*"]
    },
    install_requires=INSTALL_REQUIRES,
)