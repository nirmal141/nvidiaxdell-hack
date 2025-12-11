#!/usr/bin/env python3
"""Application runner script."""
import uvicorn
from app.config import config

if __name__ == "__main__":
    # Disable reload when using local VLM (model takes 1min to load)
    use_reload = config.debug and not config.video.use_local_vlm
    
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=use_reload,
        log_level="info"
    )

