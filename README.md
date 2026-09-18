# mini-rag-app
This is a minimal implementation of the RAG model for question answering.

## Requirements

### Install Miniconda and create new environment

1) Download and install Miniconda from [here](
    https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install
)
2) Create a new environment using the following command:
```bash
$ conda create --name mini-rag
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```

### Install Python

- Python 3.14 or later
```bash
$ conda install python==3.14
```

### Install the required dependencies in the requirements.txt

```bash
$ pip install -r requirements.txt
```

### Setup the environment variables

```bash
$ cp .env.example .env
```
Then assign the keys your own values.

## Run the FastAPI
Make sure you are in the /src in the terminal
```bash
$ uvicorn main:app --reload
```