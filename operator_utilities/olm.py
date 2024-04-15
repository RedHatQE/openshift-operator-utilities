from kubernetes.dynamic.exceptions import ResourceNotFoundError

from ocp_resources.catalog_source import CatalogSource
from ocp_resources.cluster_service_version import ClusterServiceVersion
from ocp_resources.subscription import Subscription


def get_csv(csv_name: str, namespace: str) -> ClusterServiceVersion:
    """
    gets csv by name

    Args:
        csv_name (str): name of the CSV
        namespace_name (str): namespace of CSV

    Returns:
        ClusterServiceVersion: CSV object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the CSV is not found
    """
    csv = ClusterServiceVersion(name=csv_name, namespace=namespace)
    if csv.exists:
        return csv
    raise ResourceNotFoundError(f"CSV: {csv_name} not found in namespace: {namespace}")


def get_subscription(subscription_name: str, namespace: str) -> Subscription:
    """
    gets subscription by name

    Args:
        subscription_name (str): name of the subscription
        namespace (str): namespace of subscription

    Returns:
        Subscription: Subscription object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the subscription is not found
    """
    subscription = Subscription(
        name=subscription_name,
        namespace=namespace,
    )
    if subscription.exists:
        return subscription
    raise ResourceNotFoundError(f"Subscription {subscription_name} not found in namespace: {namespace}")


def get_cnv_installed_csv(namespace: str, subscription_name: str) -> ClusterServiceVersion:
    """
    gets installed csv associated with openshift-virtualization

    Args:
        subscription_name (str): name of the openshift-virtualization subscripion
        namespace (str): openshift-virtualization operator namespace

    Returns:
        ClusterServiceVersion: CSV object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the CSV is not found
    """
    cnv_subscription = get_subscription(
        namespace=namespace,
        subscription_name=subscription_name,
    )
    return get_csv(
        csv_name=cnv_subscription.instance.status.installedCSV,
        namespace=namespace,
    )


def get_catalog_source(catalogsource_name: str, catalogsource_namespace: str) -> CatalogSource:
    """
    gets catalogsource by name

    Args:
        catalogsource_name (str): name of the catalogsource
        catalogsource_namespace (str): namespace of catalogsource

    Returns:
        CatalogSource: CatalogSource object

    Raises:
        ResourceNotFoundError: Raises ResourceNotFoundError if the namespace is not found
    """
    catalog_source = CatalogSource(
        name=catalogsource_name,
        namespace=catalogsource_namespace,
    )
    if catalog_source.exists:
        return catalog_source

    raise ResourceNotFoundError(f"Subscription {catalogsource_name} not found in namespace: {catalogsource_namespace}")
