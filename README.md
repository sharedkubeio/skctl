# skctl
skctl is the Sharedkube's CLI tool

## Installation
It's best to install `skctl` via `pipx`:

```shell
pipx install git+https://github.com/sharedkubeio/skctl
```

## Usage

This section provides detailed instructions on how to use the skctl CLI tool.

### Example - Login and switch to a zone


```shell
$ skctl login fFeqyAxxxxxxxxW6jUKAVPSuOTYdLEOnLoMvNIenV34oqp3k3Y7Dxxxxxxxxxxxx # Login to Sharedkube
$ # A token is already saved. Do you want to override it? [y/N]: y
$ # Login successful. Token saved. Hello Patryk
$ skctl zones # List available zones
$ # ID                                    Name                    CPU  Memory    Storage    Status    Type
$ # 71xxxx28-xxxx-4835-9868-xxxxxx6de5ea  my-company-dev          1    2Gi       10G        draft     Zone.Namespace.NamespaceRQuota
$ # 0fxxxx3d-xxxx-4a47-9a74-xxxxxx25a000  my-company-prod         1    2Gi       10G        running   Zone.Namespace.NamespaceRQuota
$ skctl switch my-company-prod # Switch to a zone
$ # Updated kubeconfig for zone: my-company-prod
$ kubectl get pods # Check if it works
$ # No resources found in sk-roundmelon namespace. # It works!
```

### Commands

#### `login`

Log in to the Sharedkube service using an authentication token.

**Usage:**

```shell
skctl login <64char_token>
```

**Example:**

```shell
skctl login fdg5r5rgs5gs5hgs45y45ys45y54ys34vcv3s3vs3v3svsv3ea4tetv4aet4t4tt
```

This command verifies your token with the API and saves it locally if it is valid.

#### `zones`

List all available zones.

**Usage:**

```shell
skctl zones
```

This command fetches and displays a list of zones with details such as ID, Name, CPU, Memory, Storage, Status, and Type.

#### `switch`

Switch to a specific zone by updating the current context in the kubeconfig file.

**Usage:**

```shell
skctl switch <zone_name>
```

**Example:**

```shell
skctl switch my_zone
```

This command updates your kubeconfig to set the specified zone as the current context.

#### `get_token`

Retrieve the authentication token for kubectl for a specific zone. This command is hidden and primarily used for internal purposes.

**Usage:**

```shell
skctl get_token <zone_id>
```

**Example:**

```shell
skctl get_token 12345
```

This command outputs the authentication token required for kubectl to interact with the specified zone.

### Options

#### `--api-host`

Specify a different API host if needed. The default is `https://api.sharedkube.io/api/v1`.

**Usage:**

```shell
skctl --api-host <url> <command>
```

**Example:**

```shell
skctl --api-host https://custom.api.host/api/v1 zones
```

#### `--debug/--no-debug`

Enable or disable debug mode. Debug mode provides more detailed logging information.

**Usage:**

```shell
skctl --debug <command>
```

**Example:**

```shell
skctl --debug login your_authentication_token
```

This option helps in troubleshooting by providing detailed logs.

### Configuration Files

#### Token Configuration

The token is stored in a configuration file located at `~/.sharedkube_token`. This file is created and managed by the CLI tool automatically.

#### Kubeconfig

The kubeconfig file is casually located at `~/.kube/config`. The CLI tool updates this file to manage Kubernetes contexts for different zones.
