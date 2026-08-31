# mini-rag
This is a minimal implementation of the RAG model for question answering.

## Requirements
- Python 3.8 or later

### Install python using Miniconda

1) Download and install Miniconda from [here](
    https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install
)
2) Create a new environment using the following command:
```bash
$ conda create --name mini-rag python=3.8
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```

### (optional) Setup your command line interface for better readability
```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Installation

### Install the required packages

```bash
$ pip install -r requirements.txt
```
### Setup the environment variables
```bash
$ cp .env.example .env
```

Set your environment variables in the `.env` file. Like `OPEN_AI_KEY` value.

## Run the FastAPI

```bash
$ uvicorn main:app --host 0.0.0.0 --port 5000
```