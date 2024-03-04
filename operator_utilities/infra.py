from ocp_resources.namespace import Namespace
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from pytest_testconfig import config as py_config
from operator_utilities.operator import get_subscription, get_csv


def get_namespace(name):
    namespace = Namespace(name=name)
    if namespace.exists:
        return namespace
    raise ResourceNotFoundError(f"Namespace: {name} not found")


def get_cnv_installed_csv(namespace):
    cnv_subscription = get_subscription(
        namespace=namespace,
        subscription_name=py_config["hco_subscription"],
    )
    return get_csv(
        csv_name=cnv_subscription.instance.status.installedCSV,
        namespace=namespace,
    )
