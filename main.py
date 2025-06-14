import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from scapper import AsyncNewsAPI, NewsConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class NewsResponse(BaseModel):
    success: bool
    category: str
    data: List[Dict[str, Any]]
    error: Optional[str] = None
    total_articles: int = Field(..., description="Total number of articles returned")
    timestamp: str = Field(..., description="Response timestamp")


class MultiCategoryResponse(BaseModel):
    success: bool
    categories: Dict[str, Dict[str, Any]]
    timestamp: str = Field(..., description="Response timestamp")
    total_categories: int = Field(..., description="Number of categories processed")


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    timestamp: str
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime: Optional[str] = None


app = FastAPI(
    title="Inshorts News API",
    description="Async FastAPI wrapper for Inshorts news fetching with enhanced performance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app_start_time = datetime.utcnow()
news_api_instance = None


@app.on_event("startup")
async def startup_event():
    global news_api_instance
    news_api_instance = AsyncNewsAPI()
    await news_api_instance.__aenter__()
    logger.info("Inshort News API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    global news_api_instance
    if news_api_instance:
        await news_api_instance.__aexit__(None, None, None)
    logger.info("Inshort News API shut down")


def get_current_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


@app.get("/", response_model=HealthResponse)
async def root():
    uptime = str(datetime.utcnow() - app_start_time)
    return HealthResponse(
        status="active",
        timestamp=get_current_timestamp(),
        uptime=uptime
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    uptime = str(datetime.utcnow() - app_start_time)
    return HealthResponse(
        status="healthy",
        timestamp=get_current_timestamp(),
        uptime=uptime
    )


@app.get("/categories")
async def get_categories():
    categories = {
        "available_categories": [
            "all",
            "business",
            "sports",
            "technology",
            "entertainment",
            "science",
            "politics",
            "world"
        ],
        "timestamp": get_current_timestamp()
    }
    return categories


@app.get("/news/{category}", response_model=NewsResponse)
async def get_news_by_category(
        category: str,
        max_limit: int = Query(default=10, ge=1, le=100, description="Maximum number of articles (1-100)")
):
    try:
        if max_limit < 1 or max_limit > 100:
            raise HTTPException(status_code=400, detail="max_limit must be between 1 and 100")

        logger.info(f"Fetching news for category: {category}, limit: {max_limit}")

        news_data = await news_api_instance.get_news(category, max_limit)

        if not news_data['success']:
            raise HTTPException(status_code=400, detail=news_data.get('error', 'Unknown error'))

        limited_data = news_data['data'][:max_limit]

        response = NewsResponse(
            success=news_data['success'],
            category=news_data['category'],
            data=limited_data,
            error=news_data.get('error'),
            total_articles=len(limited_data),
            timestamp=get_current_timestamp()
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news for category {category}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/news/multiple")
async def get_multiple_categories_news(
        categories: str = Query(..., description="Comma-separated list of categories"),
        max_limit: int = Query(default=10, ge=1, le=50, description="Maximum articles per category (1-50)")
):
    try:
        if max_limit < 1 or max_limit > 50:
            raise HTTPException(status_code=400, detail="max_limit must be between 1 and 50")

        category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]

        if len(category_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 categories allowed per request")

        if not category_list:
            raise HTTPException(status_code=400, detail="At least one category must be provided")

        logger.info(f"Fetching news for categories: {category_list}, limit: {max_limit}")

        news_data = await news_api_instance.get_multiple_categories(category_list, max_limit)

        for category, data in news_data.items():
            if data['success'] and 'data' in data:
                data['data'] = data['data'][:max_limit]

        response = MultiCategoryResponse(
            success=True,
            categories=news_data,
            timestamp=get_current_timestamp(),
            total_categories=len(news_data)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching multiple categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/search", response_model=NewsResponse)
async def search_news(
        query: str = Query(..., min_length=3, description="Search query (minimum 3 characters)"),
        category: str = Query(default="all", description="Category to search within"),
        max_limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results")
):
    try:
        if max_limit < 1 or max_limit > 50:
            raise HTTPException(status_code=400, detail="max_limit must be between 1 and 50")

        news_data = await news_api_instance.get_news(category, max_limit * 3)

        if not news_data['success']:
            raise HTTPException(status_code=400, detail=news_data.get('error', 'Unknown error'))

        filtered_articles = []
        query_lower = query.lower()

        for article in news_data['data']:
            if (query_lower in article.get('title', '').lower() or
                    query_lower in article.get('content', '').lower()):
                filtered_articles.append(article)
                if len(filtered_articles) >= max_limit:
                    break

        response = NewsResponse(
            success=True,
            category=f"search:{query}",
            data=filtered_articles,
            total_articles=len(filtered_articles),
            timestamp=get_current_timestamp()
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/trending", response_model=NewsResponse)
async def get_trending_news(
        max_limit: int = Query(default=20, ge=1, le=100, description="Maximum number of trending articles")
):
    if max_limit < 1 or max_limit > 100:
        raise HTTPException(status_code=400, detail="max_limit must be between 1 and 100")
    return await get_news_by_category("all", max_limit)


@app.get("/stats")
async def get_api_stats():
    uptime = str(datetime.utcnow() - app_start_time)

    return {
        "api_version": "1.0.0",
        "uptime": uptime,
        "timestamp": get_current_timestamp(),
        "features": {
            "async_support": True,
            "concurrent_requests": True,
            "multiple_categories": True,
            "search_support": True,
            "rate_limiting": False
        },
        "limits": {
            "max_articles_per_request": 100,
            "max_categories_per_request": 10,
            "concurrent_request_limit": NewsConfig.MAX_CONCURRENT_REQUESTS
        }
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Endpoint not found",
            timestamp=get_current_timestamp(),
            details=f"The requested endpoint {request.url.path} was not found"
        ).dict()
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            timestamp=get_current_timestamp(),
            details="An unexpected error occurred"
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
