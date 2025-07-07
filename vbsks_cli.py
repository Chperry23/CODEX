#!/usr/bin/env python
from __future__ import annotations

import os
import click

from vbsks import VBSKSEasy


@click.group()
@click.option(
    "--db-folder",
    default=lambda: os.environ.get("VBSKS_DB_FOLDER"),
    help="Database folder (or set VBSKS_DB_FOLDER)",
)
@click.option(
    "--master-password",
    default=lambda: os.environ.get("VBSKS_MASTER_PASSWORD"),
    prompt=os.environ.get("VBSKS_MASTER_PASSWORD") is None,
    hide_input=True,
)
@click.pass_context
def cli(ctx, db_folder: str, master_password: str) -> None:
    ctx.obj = VBSKSEasy(db_folder=db_folder, master_password=master_password)


@cli.command()
@click.pass_obj
def init(v: VBSKSEasy) -> None:
    click.echo("Database initialised at %s" % v.db_folder)


@cli.command()
@click.option("--key-id", required=True)
@click.option("--data", prompt=True, hide_input=True)
@click.pass_obj
def store(v: VBSKSEasy, key_id: str, data: str) -> None:
    v.store_key(key_id, data)
    click.echo(f"Stored key {key_id}")


@cli.command()
@click.option("--key-id", required=True)
@click.pass_obj
def retrieve(v: VBSKSEasy, key_id: str) -> None:
    secret = v.retrieve_key(key_id)
    if secret:
        click.echo(secret)
    else:
        click.echo("Key not found")


@cli.command()
@click.pass_obj
def list(v: VBSKSEasy) -> None:
    for key_id in v.list_keys():
        click.echo(key_id)


@cli.command()
@click.pass_obj
def reconfigure(v: VBSKSEasy) -> None:
    v.reconfigure()
    click.echo("Reconfiguration complete")


@cli.command()
@click.option("--key-id", required=True)
@click.pass_obj
def delete(v: VBSKSEasy, key_id: str) -> None:
    if v.delete_key(key_id):
        click.echo(f"Deleted key {key_id}")
    else:
        click.echo("Key not found")


if __name__ == "__main__":
    cli()
