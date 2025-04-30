import sys
import logging
import uvicorn
import os
 
logger = logging.getLogger(__name__)
if __name__ == "__main__":
 if "--prod" in sys.argv or os.environ.get("PROD", False):
        print("Running in production mode")
        uvicorn.run(
            "src.server:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8081)),
            root_path=os.environ.get("BASE_PATH", "/"),
            reload=False,
            workers=8,
        )
 else:
        print("Running in development mode")
        uvicorn.run(
            "src.server:app",
            host="0.0.0.0",
            root_path=os.environ.get("BASE_PATH", "/"),
            port=8000,
            workers=8,
        )