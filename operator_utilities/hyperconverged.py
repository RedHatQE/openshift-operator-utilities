import json
from typing import Optional
from simple_logger.logger import get_logger

from kubernetes.dynamic.exceptions import ResourceNotFoundError
from ocp_resources.hyperconverged import HyperConverged
from ocp_resources.resource import Resource
from operator_utilities.exceptions import (
    HyperconvergedNotHealthyCondition,
    HyperconvergedSystemHealthException,
)

LOGGER = get_logger(name=__name__)


def get_hyperconverged_resource(hyperconverged_name: HyperConverged, namespace_name: str) -> HyperConverged:
    """
    gets hyperconverged CR by name

    Args:
        hyperconverged_name (str): name of the hyperconverged CR
        namespace_name (str): namespace of hyperconverged CR

    Returns:
        HyperConverged: Hyperconverged CR object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the Hyperconverged CR is not found
    """
    hco = HyperConverged(name=hyperconverged_name, namespace=namespace_name)
    if hco.exists:
        return hco
    raise ResourceNotFoundError(f"Hyperconverged resource not found in {namespace_name}")


def assert_hyperconverged_health(
    hyperconverged: HyperConverged,
    hyperconverged_status_conditions: Optional[dict] = None,
    system_health_status: Optional[str] = None,
) -> None:
    """
    Validates hyperconverged CR is in a healthy condition.
    Hyperconverged CR's Available, ReconcileComplete, Upgradeable conditions are True and Progressing and
    Degraded conditions are False:

    Args:
         hyperconverged (HyperConverged): hyperconverged CR object

         hyperconverged_status_conditions (dict):
            Dictionary with condition type and the respective healthy condition
                status: Example: {"Available": "True", ...}
         system_health_status (str): expected systemHealthStatus for hyperconvered CR

    Raises:
        HyperconvergedNotHealthyCondition: if hyperconverged CR's status conditions are not healthy
        HyperconvergedSystemHealthException: If systemHealthStatus indicates not healthy
    """
    if not hyperconverged_status_conditions:
        hyperconverged_status_conditions = {
            Resource.Condition.AVAILABLE: Resource.Condition.Status.TRUE,
            Resource.Condition.PROGRESSING: Resource.Condition.Status.FALSE,
            Resource.Condition.RECONCILE_COMPLETE: Resource.Condition.Status.TRUE,
            Resource.Condition.DEGRADED: Resource.Condition.Status.FALSE,
            Resource.Condition.UPGRADEABLE: Resource.Condition.Status.TRUE,
        }
    hyperconverged_obj_status = hyperconverged.instance.status

    health_mismatch_conditions = [
        condition
        for condition in hyperconverged_obj_status.conditions
        if condition.type in hyperconverged_status_conditions
        and hyperconverged_status_conditions[condition.type] != condition.status
    ]
    if health_mismatch_conditions:
        raise HyperconvergedNotHealthyCondition(
            "Hyperconverged status condition unhealthy "
            f"expected: {json.dumps(hyperconverged_status_conditions, indent=3)}:"
            f"actual: {json.dumps(health_mismatch_conditions, indent=3)}"
        )

    if system_health_status and hyperconverged_obj_status.systemHealthStatus != system_health_status:
        raise HyperconvergedSystemHealthException(
            f"Hyperconverged systemHealthStatus expected: {system_health_status},"
            f" actual: {hyperconverged_obj_status.systemHealthStatus}"
        )
