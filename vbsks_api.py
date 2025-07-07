#!/usr/bin/env python
from __future__ import annotations

import argparse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from vbsks import VBSKSEasy

app = FastAPI()


class InitParams(BaseModel):
    db_folder: str
    master_password: str


class StoreRequest(BaseModel):
    key_id: str
    data: str


class RetrieveRequest(BaseModel):
    key_id: str


def get_manager(db_folder: str, master_password: str) -> VBSKSEasy:
    return VBSKSEasy(db_folder=db_folder, master_password=master_password)


@app.post("/store")
def store(req: StoreRequest, db_folder: str, master_password: str):
    v = get_manager(db_folder, master_password)
    v.store_key(req.key_id, req.data)
    return {"status": "stored"}


@app.post("/retrieve")
def retrieve(req: RetrieveRequest, db_folder: str, master_password: str):
    v = get_manager(db_folder, master_password)
    data = v.retrieve_key(req.key_id)
    if data is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"data": data}


@app.get("/list")
def list_keys(db_folder: str, master_password: str):
    v = get_manager(db_folder, master_password)
    return {"keys": v.list_keys()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-folder", required=True)
    parser.add_argument("--master-password", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    from uvicorn import run

    run(
        "vbsks_api:app",
        host=args.host,
        port=args.port,
        reload=False,
        factory=False,
    )
