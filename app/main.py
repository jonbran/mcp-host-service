"""Main entry point for the MCP service."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.api.models_router import router as models_router
from app.auth.init import init_admin_user
from app.auth.router import router as auth_router
from app.config.config import load_config
from app.utils.env import load_env

# Load environment variables
env = load_env()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path("config/config.json")
config = load_config(config_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application lifecycle events."""
    # Startup: Initialize services
    logger.info("Starting MCP service")
    logger.info(f"Configuration loaded from {config_path}")
    logger.info(f"API running on {config.api.host}:{config.api.port}")
    
    # Initialize admin user
    init_admin_user()
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down MCP service")

# Create FastAPI app with lifespan
app = FastAPI(
    title="MCP Service",
    description="MCP Host/Client/Service for Hugging Face models",
    version="0.1.0",
    lifespan=lifespan,
)

# Add routers
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(models_router, prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=True,
    )
