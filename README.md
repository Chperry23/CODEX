# Vector-Based Secure Key Storage (VBSKS)

This repository contains the initial implementation of **VBSKS**, a quantum resistant key storage
system based on high‑dimensional vector spaces.  The goal of this project is to build a
commercial‑grade application that exposes VBSKS through a Python library, a command line tool
and a REST API that can be integrated with front‑end clients.

This repository currently provides a minimal prototype consisting of:

- a Python package (`vbsks`) with the core logic
- a command line interface (`vbsks_cli.py`)
- a small REST API server (`vbsks_api.py`)

The project is in an early stage but demonstrates how keys can be stored as encrypted vectors
surrounded by noise, making them difficult to locate without the correct metadata.

## Quick start

Create a virtual environment and install the requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Initialise a new database folder and store a test key (the CLI reads
`VBSKS_DB_FOLDER` and `VBSKS_MASTER_PASSWORD` if set):

```bash
python vbsks_cli.py init --db-folder mydb
python vbsks_cli.py store --key-id example --db-folder mydb
python vbsks_cli.py retrieve --key-id example --db-folder mydb
python vbsks_cli.py delete --key-id example --db-folder mydb
```

Run the REST API (defaults can be provided via environment variables):

```bash
export VBSKS_DB_FOLDER=mydb
export VBSKS_MASTER_PASSWORD=mypassword
python vbsks_api.py
```

### API usage

The REST API exposes the following endpoints:

```
POST  /store       {"key_id": "id", "data": "secret"}
POST  /retrieve    {"key_id": "id"}
GET   /list
DELETE /delete     {"key_id": "id"}
```

For front-end applications, the server allows cross-origin requests.

## Project structure

- **vbsks/** – Python package implementing the core components
- **vbsks_cli.py** – command line interface for basic operations
- **vbsks_api.py** – simple FastAPI server exposing the library
- **requirements.txt** – runtime dependencies

## Security concept

VBSKS stores each secret as a vector embedded in a larger set of random noise vectors.
The mapping between keys and their locations is encrypted with a master password.
Periodic reconfiguration can move vectors to new positions to thwart long term analysis.

This prototype is simplified but sets the foundation for a commercial application with
additional features such as Shamir secret sharing, hardware key storage and more robust auditing.

