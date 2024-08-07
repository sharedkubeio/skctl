#!/usr/bin/env python3

import json
import logging
from pathlib import Path

import click
import requests
import yaml
from requests.auth import AuthBase
from tabulate import tabulate

CONFIG_FILE = Path.home() / ".sharedkube_token"
KUBECONFIG_FILE = Path.home() / ".kube" / "config"


class BearerAuth(AuthBase):
    """
    Bearer authentication for requests
    """
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


def save_token(token):
    """
    Save token to config file
    :param token:
    :return:
    """
    with open(CONFIG_FILE, 'w') as f:
        f.write(token)


def load_token():
    """
    Load token from config file
    :return:
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return f.read().strip()
    return None


def handle_error(response):
    """
    Handle error response from API
    :param response:
    :return:
    """
    if response is None:
        click.secho(f"{click.style('Error:', fg='red')} Could not connect to the API host.", fg="white")
        return
    try:
        error_message = response.json().get('message', 'Unknown error occurred')
    except ValueError:
        error_message = response.text
    click.secho(f"{click.style('Error:', fg='red')} {error_message}", fg="white")


def update_kubeconfig(kubeconfig_data):
    """
    Update kubeconfig file with new context, cluster and user
    :param kubeconfig_data: contains new context, cluster and user for particular zone
    """
    if not KUBECONFIG_FILE.exists():
        KUBECONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(KUBECONFIG_FILE, 'w') as f:
            yaml.dump({"apiVersion": "v1", "clusters": [], "contexts": [], "current-context": "", "kind": "Config",
                       "preferences": {}, "users": []}, f)

    with open(KUBECONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)

    # Update or add context
    context_exists = False
    for context in config["contexts"]:
        if context["name"] == kubeconfig_data["contexts"][0]["name"]:
            context["context"] = kubeconfig_data["contexts"][0]["context"]
            context_exists = True
            break
    if not context_exists:
        config["contexts"].append(kubeconfig_data["contexts"][0])

    # Update or add cluster
    cluster_exists = False
    for cluster in config["clusters"]:
        if cluster["name"] == kubeconfig_data["clusters"][0]["name"]:
            cluster["cluster"] = kubeconfig_data["clusters"][0]["cluster"]
            cluster_exists = True
            break
    if not cluster_exists:
        config["clusters"].append(kubeconfig_data["clusters"][0])

    # Update or add user
    user_exists = False
    for user in config["users"]:
        if user["name"] == kubeconfig_data["users"][0]["name"]:
            user["user"] = kubeconfig_data["users"][0]["user"]
            user_exists = True
            break
    if not user_exists:
        config["users"].append(kubeconfig_data["users"][0])

    config["current-context"] = kubeconfig_data["current-context"]

    with open(KUBECONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


@click.group()
@click.option("--api-host", default="https://api.sharedkube.io/api/v1", help="Specify a different API host.")
@click.option("--debug/--no-debug", default=False, help="Enable or disable debug mode.")
@click.pass_context
def cli(ctx, api_host, debug):
    """CLI tool for Sharedkube"""
    ctx.ensure_object(dict)
    ctx.obj["API_HOST"] = api_host
    ctx.obj["DEBUG"] = debug

    # Configure logging
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@cli.command()
@click.argument("token")
@click.pass_context
def login(ctx, token):
    """Login using token"""
    api_host = ctx.obj["API_HOST"]
    existing_token = load_token()

    try:
        verify_resp = requests.post(f"{api_host}/tokens/verify", json={"token": token})
        verify_resp.raise_for_status()
        user_info = verify_resp.json()
        if existing_token:
            if not click.confirm(click.style("A token is already saved. Do you want to override it?", fg="yellow")):
                click.secho(click.style("Login aborted. Existing token was not overridden.", fg="red"))
                return
        save_token(token)
        click.secho(
            f"Login successful. {click.style('Token saved.', fg='green')} Hello {click.style(user_info['first_name'], fg='blue')}",
            fg="white")
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 401:
            click.secho(f"{click.style('Error:', fg='red')} Invalid token.", fg="white")
        else:
            handle_error(e.response)


@cli.command()
@click.pass_context
def zones(ctx):
    """List all zones"""
    token = load_token()
    if not token:
        click.secho(f"{click.style('Error:', fg='red')} No token found. Please login first.", fg="white")
        return

    api_host = ctx.obj["API_HOST"]
    try:
        zones_resp = requests.get(f"{api_host}/zones", auth=BearerAuth(token))
        zones_resp.raise_for_status()
        zones = zones_resp.json()

        if not zones:
            click.secho("No zones found.", fg="yellow")
        else:
            headers = ["ID", "Name", "CPU", "Memory", "Storage", "Status", "Type"]
            table = [
                [
                    zone["id"],
                    zone["name"],
                    f"{zone['resource_quota_size']['cpu']}",
                    f"{zone['resource_quota_size']['memory']}Gi",
                    f"{zone['resource_quota_size']['storage']}G",
                    zone["status"],
                    zone["type"]
                ]
                for zone in zones
            ]
            click.echo(tabulate(table, headers, tablefmt="plain"))
    except requests.exceptions.RequestException as e:
        handle_error(e.response)


@cli.command()
@click.argument("zone_name")
@click.pass_context
def switch(ctx, zone_name):
    """Update current-context in kubeconfig for particular zone"""
    token = load_token()
    if not token:
        click.secho(f"{click.style('Error:', fg='red')} No token found. Please login first.", fg="white")
        return

    api_host = ctx.obj["API_HOST"]
    try:
        zone_resp = requests.get(f"{api_host}/zones/name/{zone_name}", auth=BearerAuth(token))
        logging.debug(f"zone_resp: {zone_resp.json()}")
        zone_resp.raise_for_status()
        zone_id = zone_resp.json()["id"]

        kubeconfig_resp = requests.get(f"{api_host}/zones/{zone_id}/kubeconfig", auth=BearerAuth(token))
        logging.debug(f"kubeconfig_resp: {kubeconfig_resp.json()}")
        kubeconfig_resp.raise_for_status()
        kubeconfig_data = kubeconfig_resp.json()

        update_kubeconfig(kubeconfig_data)
        click.secho(f"Updated kubeconfig for zone: {click.style(zone_name, fg='blue')}", fg="white")
    except requests.exceptions.RequestException as e:
        handle_error(e.response)


@cli.command(hidden=True)
@click.argument("zone_id")
@click.pass_context
def get_token(ctx, zone_id):
    """Get authentication token for kubectl"""
    token = load_token()
    if not token:
        click.secho(f"{click.style('Error:', fg='red')} No token found. Please login first.", fg="white")
        return

    api_host = ctx.obj["API_HOST"]
    try:
        token_resp = requests.get(f"{api_host}/zones/{zone_id}/token", auth=BearerAuth(token))
        token_resp.raise_for_status()
        token_data = token_resp.json()
        click.echo(json.dumps(token_data, indent=4) + "\n")
    except requests.exceptions.RequestException as e:
        handle_error(e.response)


if __name__ == "__main__":
    cli()
