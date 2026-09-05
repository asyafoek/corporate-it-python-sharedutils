import base64
import json
import os

from kubernetes import client, config

def get_secret(secret_name, namespace, key, encoding="UTF-8"):
    config.load_incluster_config()

    v1 = client.CoreV1Api()

    secret = v1.read_namespaced_secret(
        name=secret_name,
        namespace=namespace
    )

    value = base64.b64decode(
        secret.data[key]
    ).decode(encoding)

    return value

def get_current_namespace():
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
        return f.read().strip()
