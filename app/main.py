from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.agents import router
from app.routes import users
from app.routes.nft_agents import router as nft_router

from app.routes.news_portfolio_agents import router as news_router
from app.routes.defi import router as defi_router

# Initialize FastAPI app
app = FastAPI(
    title="Crypto Agent API",
    description="API for cryptocurrency analysis and graphing",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api")
app.include_router(users.router)
app.include_router(nft_router)
app.include_router(news_router)
app.include_router(defi_router)

# Root endpoint


@app.get("/")
async def root():
    return {"message": "Welcome to Crypto Agent API. Use /api endpoints to access functionality."}

# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Get host and port from environment variables
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
