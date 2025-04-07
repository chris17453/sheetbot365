from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sheetbot365",
    version="1.0.0",
    author="Charles Watkins",
    author_email="chris@watkinslabs.com",
    description="An office365 tool for automating AP PO Tracking VIA XLSX Spreadsheets. It retrieves, stores and processes email server side to populate a Spreadsheet with all PO's with totals and relivant details.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chris17453/sheetbot365",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "sheetbot365=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pymssql>=2.2.5",
        "pyyaml>=6.0",
        "msal>=1.20.0",
        "psutil>=5.9.4",
        "requests>=2.28.2",
    ],
)