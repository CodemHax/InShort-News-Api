# Inshorts News API

A high-performance async FastAPI wrapper for fetching news from Inshorts.com with enhanced features, concurrent processing, and comprehensive error handling.

## 🚀 Features

- **Async/Await Architecture**: Built with modern Python async patterns for maximum performance
- **Concurrent Processing**: Fetch multiple news categories simultaneously
- **FastAPI Integration**: Auto-generated interactive API documentation
- **Rate Limiting Ready**: Built-in support for request limiting and throttling
- **Error Handling**: Comprehensive error responses with detailed logging
- **Docker Support**: Ready for containerized deployment
- **CORS Enabled**: Cross-origin request support for web applications
- **Input Validation**: Pydantic models ensure data integrity
- **Health Monitoring**: Built-in health check endpoints

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- pip (Python package installer)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/CodemHax/inshorts-news-api.git
cd inshorts-news-api

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --port 8000
```

## Quick Start
[Content for Quick Start]

## API Endpoints

The API provides the following endpoints:

### Health & Status

*   **`GET /`**
    *   Description: Root endpoint, returns the current status of the API, including uptime.
    *   Response: `HealthResponse`
        ```json
        {
          "status": "active",
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC",
          "version": "1.0.0",
          "uptime": "d days, HH:MM:SS.ffffff"
        }
        ```

*   **`GET /health`**
    *   Description: Health check endpoint, returns the current health status of the API, including uptime.
    *   Response: `HealthResponse`
        ```json
        {
          "status": "healthy",
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC",
          "version": "1.0.0",
          "uptime": "d days, HH:MM:SS.ffffff"
        }
        ```

*   **`GET /stats`**
    *   Description: Provides statistics about the API, including version, uptime, features, and limits.
    *   Response:
        ```json
        {
          "api_version": "1.0.0",
          "uptime": "d days, HH:MM:SS.ffffff",
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC",
          "features": {
            "async_support": true,
            "concurrent_requests": true,
            "multiple_categories": true,
            "search_support": true,
            "rate_limiting": false
          },
          "limits": {
            "max_articles_per_request": 100,
            "max_categories_per_request": 10,
            "concurrent_request_limit": 20 
          }
        }
        ```

### News Categories

*   **`GET /categories`**
    *   Description: Retrieves a list of available news categories.
    *   Response:
        ```json
        {
          "available_categories": [
            "all",
            "business",
            "sports",
            "technology",
            "entertainment",
            "health",
            "science",
            "politics",
            "world"
          ],
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC"
        }
        ```

### Fetching News

*   **`GET /news/{category}`**
    *   Description: Fetches news articles for a specified category.
    *   Path Parameters:
        *   `category` (string, required): The news category to fetch (e.g., `business`, `sports`, `all`).
    *   Query Parameters:
        *   `max_limit` (integer, optional, default: 10, min: 1, max: 100): Maximum number of articles to return.
    *   Response: `NewsResponse`
        ```json
        {
          "success": true,
          "category": "technology",
          "data": [
            {
              "title": "Sample Article Title",
              "content": "Sample article content...",
              "author": "Author Name",
              "read_more_url": "http://example.com/news/article",
              "image_url": "http://example.com/image.jpg",
              "timestamp": "Article Timestamp"
            }
          ],
          "error": null,
          "total_articles": 10,
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC"
        }
        ```

*   **`GET /news/multiple`**
    *   Description: Fetches news articles for multiple categories simultaneously.
    *   Query Parameters:
        *   `categories` (string, required): Comma-separated list of news categories (e.g., `business,sports,technology`). Maximum 10 categories.
        *   `max_limit` (integer, optional, default: 10, min: 1, max: 50): Maximum number of articles to return per category.
    *   Response: `MultiCategoryResponse`
        ```json
        {
          "success": true,
          "categories": {
            "business": {
              "success": true,
              "category": "business",
              "data": [ ],
              "error": null,
              "total_articles": 5 
            },
            "sports": {
              "success": true,
              "category": "sports",
              "data": [ ],
              "error": null,
              "total_articles": 7
            }
        
          },
          "timestamp": "YYYY-MM-DD HH:MM:SS UTC",
          "total_categories": 2 
        }
        ```

*   **`GET /search`**
    *   Description: Searches news articles based on a query string within a specified category (or all categories).
    *   Query Parameters:
        *   `query` (string, required, min_length: 3): The search term (minimum 3 characters).
        *   `category` (string, optional, default: `all`): The category to search within.
        *   `max_limit` (integer, optional, default: 10, min: 1, max: 50): Maximum number of search results to return.
    *   Response: `NewsResponse` (Category will be `search:{query}`)

*   **`GET /trending`**
    *   Description: Fetches trending news articles. This is effectively an alias for `/news/all`.
    *   Query Parameters:
        *   `max_limit` (integer, optional, default: 20, min: 1, max: 100): Maximum number of trending articles to return.
    *   Response: `NewsResponse` (Category will be `all`)

### Error Responses

In case of errors (e.g., invalid input, server issues), the API returns a JSON response with the following structure:

*   **`ErrorResponse`**
    ```json
    {
      "success": false,
      "error": "Error message (e.g., Endpoint not found, Internal server error)",
      "timestamp": "YYYY-MM-DD HH:MM:SS UTC",
      "details": "Optional additional details about the error"
    }
    ```
    Common HTTP status codes used:
    *   `400 Bad Request`: For client-side errors like invalid parameters.
    *   `404 Not Found`: If the requested endpoint doesn't exist.
    *   `500 Internal Server Error`: For unexpected server-side issues.

You can access the interactive API documentation (Swagger UI) at `/docs` and ReDoc at `/redoc` when the application is running.

## Usage Examples
[Content for Usage Examples]

## Configuration
[Content for Configuration]

## Contributing
[Content for Contributing]

## License
[Content for License]
