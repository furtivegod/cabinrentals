"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="Cabin Rentals API",
    description="AI-Driven Property Management Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cabin Rentals of Georgia API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


# Import API routes
from app.api.v1 import blogs, faqs, policies, about_us, taxonomy

# Blog and FAQ routes
app.include_router(blogs.router, prefix="/api/v1", tags=["blogs"])
app.include_router(faqs.router, prefix="/api/v1", tags=["faqs"])

# Policies and About Us routes
app.include_router(policies.router, prefix="/api/v1", tags=["policies"])
app.include_router(about_us.router, prefix="/api/v1", tags=["about-us"])

# Taxonomy routes
app.include_router(taxonomy.router, prefix="/api/v1", tags=["taxonomy"])

# Other routes (commented out for now)
# from app.api.v1 import properties, bookings, quotes, content_blocks, chat, sync
# app.include_router(properties.router, prefix="/api/v1", tags=["properties"])
# app.include_router(bookings.router, prefix="/api/v1", tags=["bookings"])
# app.include_router(quotes.router, prefix="/api/v1", tags=["quotes"])
# app.include_router(content_blocks.router, prefix="/api/v1", tags=["content"])
# app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
# app.include_router(sync.router, prefix="/api/v1", tags=["sync"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

