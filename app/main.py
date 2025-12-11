"""FastAPI main application entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sentio",
    description="Ask questions about video content using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static path for serving files
static_path = Path(__file__).parent / "static"

# Include API routes FIRST (before static mount)
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main web application."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Video Q&A</title></head>
    <body>
        <h1>Video Q&A Application</h1>
        <p>Frontend not found. Please ensure static files are present.</p>
    </body>
    </html>
    """)


# Mount static files AFTER routes (so API routes take precedence)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Video Q&A Application...")
    
    # Ensure directories exist
    config.videos_dir.mkdir(parents=True, exist_ok=True)
    Path(config.milvus.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Videos directory: {config.videos_dir}")
    logger.info(f"Milvus database: {config.milvus.db_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Video Q&A Application...")
