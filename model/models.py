from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# =============================
# Input schema models
# =============================

class AuthParams(BaseModel):
    """Authentication parameters."""
    
    client_id: str = Field(
        description="Client ID."
    )
    client_secret: str = Field(
        description="Client secret."
    )

class ResourceStatusParams(BaseModel):
    """Get resource status for a specific stream tenant."""

    stream_tenant_id: str = Field(
        description="Stream tenant ID."
    )

class EventStatusParams(BaseModel):
    """Get event status for a specific stream tenant."""

    stream_tenant_id: str = Field(
        description="Stream tenant ID."
    )

class DeviceStatusParams(BaseModel):
    """Get device status for a specific SSE ID."""

    sse_id: str = Field(
        description="The SSE ID of the device."
    )


# =============================
# Output schema models
# =============================

class AuthResponse(BaseModel):
    access_token: str = Field(
        description="Access token."
    )
    expires_in: int = Field(
        description="Number of seconds until the access token expires."
    )
    token_type: str = Field(
        description="Token type."
    )

class ResourceStatusResponse(BaseModel):
    request_id: str = Field(
        description="Request ID."
    )
    resource_status: Dict[str, bool] = Field(
        description="Resource status."
    )
    stream_id: str = Field(
        description="Stream ID."
    )

class EpsPerDevice(BaseModel):
    """EPS per device information."""
    
    deviceUUID: Optional[str] = Field(
        description="Device UUID, can be null."
    )
    eps: str = Field(
        description="Events per second for this device."
    )

class EventDetails(BaseModel):
    """Event details information."""
    
    event_throughput: str = Field(
        description="Event throughput rate."
    )
    events_received: bool = Field(
        description="Whether events are being received."
    )

class TenantSettings(BaseModel):
    """Tenant settings information."""
    
    days_of_storage: int = Field(
        description="Number of days data is stored."
    )
    destroyed_date_fw: Optional[str] = Field(
        description="Destroyed date for firewall, can be null."
    )
    gb_per_day: int = Field(
        description="Gigabytes per day limit."
    )
    is_fw: bool = Field(
        description="Whether this is a firewall tenant."
    )
    tenant_id: str = Field(
        description="Tenant ID."
    )
    tenant_state: str = Field(
        description="Current state of the tenant."
    )

class EventStatusResponse(BaseModel):
    """Event status response model."""
    
    eps_per_device: List[EpsPerDevice] = Field(
        description="Events per second breakdown by device."
    )
    event_details: EventDetails = Field(
        description="Event processing details."
    )
    is_eventing_plus_enabled: bool = Field(
        description="Whether eventing plus is enabled."
    )
    request_id: str = Field(
        description="Request ID."
    )
    stream_id: str = Field(
        description="Stream ID."
    )
    tenant_settings: TenantSettings = Field(
        description="Tenant configuration settings."
    )
    total_eps: str = Field(
        description="Total events per second across all devices."
    ) 

class DeviceStatusResponse(BaseModel):
    """Device status response model."""
    
    has_devices: bool = Field(
        description="Whether this tenant has devices."
    )
    request_id: str = Field(
        description="Request ID."
    )
        