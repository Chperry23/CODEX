#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vbsks import VBSKSEasy

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StoreRequest(BaseModel):
    key_id: str
    data: str


class RetrieveRequest(BaseModel):
    key_id: str


class DeleteRequest(BaseModel):
    key_id: str


def get_manager(db_folder: str | None = None, master_password: str | None = None) -> VBSKSEasy:
    db_folder = db_folder or os.environ.get("VBSKS_DB_FOLDER")
    master_password = master_password or os.environ.get("VBSKS_MASTER_PASSWORD")
    if not db_folder or not master_password:
        raise HTTPException(status_code=400, detail="Missing configuration")
    return VBSKSEasy(db_folder=db_folder, master_password=master_password)


@app.post("/store")
def store(
    req: StoreRequest,
    db_folder: str | None = None,
    master_password: str | None = None,
):
    v = get_manager(db_folder, master_password)
    v.store_key(req.key_id, req.data)
    return {"status": "stored"}


@app.post("/retrieve")
def retrieve(
    req: RetrieveRequest,
    db_folder: str | None = None,
    master_password: str | None = None,
):
    v = get_manager(db_folder, master_password)
    data = v.retrieve_key(req.key_id)
    if data is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"data": data}


@app.get("/list")
def list_keys(db_folder: str | None = None, master_password: str | None = None):
    v = get_manager(db_folder, master_password)
    return {"keys": v.list_keys()}


@app.delete("/delete")
def delete(req: DeleteRequest, db_folder: str | None = None, master_password: str | None = None):
    v = get_manager(db_folder, master_password)
    if v.delete_key(req.key_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-folder", default=os.environ.get("VBSKS_DB_FOLDER"))
    parser.add_argument("--master-password", default=os.environ.get("VBSKS_MASTER_PASSWORD"))
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
