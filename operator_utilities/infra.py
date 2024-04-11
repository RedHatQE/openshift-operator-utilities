from typing import Optional, Any

from kubernetes.dynamic import DynamicClient
from simple_logger.logger import get_logger
from timeout_sampler import TimeoutSampler, TimeoutExpiredError

from ocp_resources.namespace import Namespace

from kubernetes.dynamic.exceptions import ResourceNotFoundError, NotFoundError

from ocp_resources.pod import Pod
from operator_utilities.constants import TIMEOUT_2MIN, TIMEOUT_5SEC

LOGGER = get_logger(name=__name__)


def get_namespace(name: str) -> Namespace:
    """
    gets namespace by name

    Args:
        name(str): name of the namespace

    Returns:
        Namespace: Namespace object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the namespace is not found
    """
    namespace = Namespace(name=name)
    if namespace.exists:
        return namespace
    raise ResourceNotFoundError(f"Namespace: {name} not found")


def get_waiting_pod_container_error_status(pod: Pod) -> Any:
    """
     gets reason associated with a pod that is in waiting state

     Args:
         pod(Pod): Pod object

    Returns:
        str or None: reason for the pod to be in waiting state
    """
    pod_instance_status = pod.instance.status
    # Check the containerStatuses and if any containers is in waiting state, return that information:

    for container_status in pod_instance_status.get("containerStatuses", []):
        waiting_container = container_status.get("state", {}).get("waiting")
        if waiting_container:
            return waiting_container["reason"] if waiting_container.get("reason") else str(waiting_container)


def get_not_running_pods(pods: list, filter_pods_by_name: Optional[str] = None) -> list:
    pods_not_running = []
    for pod in pods:
        pod_instance = pod.instance
        if filter_pods_by_name and filter_pods_by_name in pod.name:
            LOGGER.warning(f"Ignoring pod: {pod.name} for pod state validations.")
            continue
        container_status_error = get_waiting_pod_container_error_status(pod=pod)
        if container_status_error:
            pods_not_running.append({pod.name: container_status_error})
        try:
            # Waits for all pods in a given namespace to be in final healthy state(running/completed).
            # We also need to keep track of pods marked for deletion as not running. This would ensure any
            # pod that was spinned up in place of pod marked for deletion, reaches healthy state before end
            # of this check
            if pod_instance.metadata.get("deletionTimestamp") or pod_instance.status.phase not in (
                pod.Status.RUNNING,
                pod.Status.SUCCEEDED,
            ):
                pods_not_running.append({pod.name: pod.status})
        except (ResourceNotFoundError, NotFoundError):
            LOGGER.warning(f"Ignoring pod {pod.name} that disappeared during cluster sanity check")
            pods_not_running.append({pod.name: "Deleted"})
    return pods_not_running


def wait_for_pods_running(
    admin_client: DynamicClient,
    namespace_name: str,
    number_of_consecutive_checks: int = 3,
    filter_pods_by_name: Optional[str] = None,
) -> Any:
    """
    Waits for all pods in a given namespace to reach Running/Completed state. To avoid catching all pods in running
    state too soon, use number_of_consecutive_checks with appropriate values.

    Args:
         admin_client(DynamicClient): Dynamic client
         namespace_name(str): name of a namespace
         number_of_consecutive_checks(int): Number of times to check for all pods in running state
         filter_pods_by_name(str): string to filter pod names by

    Raises:
        TimeoutExpiredError: Raises TimeoutExpiredError if any of the pods in the given namespace are not in Running
         state
    """
    samples = TimeoutSampler(
        wait_timeout=TIMEOUT_2MIN,
        sleep=TIMEOUT_5SEC,
        func=get_not_running_pods,
        pods=list(Pod.get(dyn_client=admin_client, namespace=namespace_name)),
        filter_pods_by_name=filter_pods_by_name,
    )
    sample = None
    try:
        current_check = 0
        for sample in samples:
            if not sample:
                current_check += 1
                if current_check >= number_of_consecutive_checks:
                    return True
            else:
                current_check = 0
    except TimeoutExpiredError:
        if sample:
            LOGGER.error(
                f"timeout waiting for all pods in namespace {namespace_name} to reach "
                f"running state, following pods are in not running state: {sample}"
            )
            raise
