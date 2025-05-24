"""Router for model provider endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends

from app.api.models_api import ModelsListResponse, ModelProviderInfo
from app.auth.models import User
from app.auth.utils import get_current_active_user

from app.model.model import ModelService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["models"])


def get_model_service() -> ModelService:
    """Get the model service instance."""
    # This depends on the model_service being initialized in the main router
    from app.api.router import model_service
    return model_service


@router.get(
    "/models",
    response_model=ModelsListResponse,
    summary="List model providers",
    description="List all available model providers including MCP servers"
)
async def list_model_providers(
    model_service: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_active_user),
):
    """List all available model providers including MCP servers."""
    # Get MCP host to add MCP servers to providers list
    from app.api.router import mcp_host
    
    providers: List[ModelProviderInfo] = []
    default_provider = "default"
    
    # Check if using model wrapper
    if not model_service.using_wrapper or not model_service.model_wrapper:
        # Return just the default model if not using wrapper
        default_model = model_service.config
        provider_info = ModelProviderInfo(
            name="default",
            provider_type=default_model.provider.value,
            model_id=default_model.model_id,
            max_sequence_length=default_model.max_sequence_length,
            temperature=default_model.temperature,
            top_p=default_model.top_p,
        )
        providers.append(provider_info)
    else:
        # Get all providers from the wrapper
        wrapper = model_service.model_wrapper
        default_provider = wrapper.default_provider_name
        
        for name in wrapper.get_available_providers():
            provider_info = wrapper.get_provider_info(name)
            if provider_info:
                providers.append(ModelProviderInfo(
                    name=name,
                    provider_type=provider_info["provider_type"],
                    model_id=provider_info["model_id"],
                    max_sequence_length=provider_info["max_sequence_length"],
                    temperature=provider_info["temperature"],
                    top_p=provider_info["top_p"],
                ))
    
    # Add MCP servers to the list
    for name, client in mcp_host.clients.items():
        providers.append(ModelProviderInfo(
            name=name,
            is_mcp_server=True,
        ))
    
    return ModelsListResponse(
        default_provider=default_provider,
        providers=providers,
    )
