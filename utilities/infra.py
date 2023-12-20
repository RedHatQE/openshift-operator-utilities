from ocp_resources.hyperconverged import HyperConverged
from kubernetes.dynamic.exceptions import ResourceNotFoundError


def get_hyperconverged_resource(namespace_name):
    hco = HyperConverged(namespace=namespace_name)
    if hco.exists:
        return hco
    raise ResourceNotFoundError(
        f"Hyperconverged resource not found in {namespace_name}"
    )
