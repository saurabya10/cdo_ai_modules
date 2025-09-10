from langchain.tools import tool
from cdo_ai_modules.client.sal_client import RestApiClient


@tool
def get_resource_status(stream_id: str) -> str:
    """Get pipeline infrastructure status for a given stream ID.
    This tools check whether the pipeline is available or not.
    """
    client = RestApiClient()
    return client.get_resource_status(stream_id)


@tool
def get_event_status(stream_id: str) -> str:
    """Get event status for a given stream ID."""
    client = RestApiClient()
    return client.get_event_status(stream_id)


@tool
def get_device_status(sse_id: str) -> str:
    """Get device status for a given SSE ID."""
    client = RestApiClient()
    return client.get_device_status(sse_id)
