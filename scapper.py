import asyncio
import datetime
import uuid
import aiohttp
import pytz
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsConfig:
    BASE_URL = 'https://inshorts.com/api/en'
    DEFAULT_MAX_LIMIT = 10
    REQUEST_TIMEOUT = 30
    MAX_CONCURRENT_REQUESTS = 5

    HEADERS = {
        'authority': 'inshorts.com',
        'accept': '*/*',
        'accept-language': 'en-GB,en;q=0.5',
        'content-type': 'application/json',
        'referer': 'https://inshorts.com/en/read',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }


class AsyncNewsAPI:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self._should_close_session = session is None
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.utc_tz = pytz.timezone('UTC')

    async def __aenter__(self):
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=NewsConfig.MAX_CONCURRENT_REQUESTS)
            timeout = aiohttp.ClientTimeout(total=NewsConfig.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=NewsConfig.HEADERS
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_session and self.session:
            await self.session.close()

    def _build_url(self, category: str) -> str:
        if category == 'all':
            return f'{NewsConfig.BASE_URL}/news'
        return f'{NewsConfig.BASE_URL}/search/trending_topics/{category}'

    def _build_params(self, category: str, max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Dict[str, Any]:
        if category == 'all':
            return {
                'category': 'all_news',
                'max_limit': max_limit,
                'include_card_data': 'true'
            }
        return {
            'category': 'top_stories',
            'max_limit': max_limit,
            'include_card_data': 'true'
        }

    def _convert_timestamp(self, timestamp: int) -> tuple[str, str]:
        try:
            dt_utc = datetime.datetime.utcfromtimestamp(timestamp / 1000)
            dt_utc = self.utc_tz.localize(dt_utc)
            dt_ist = dt_utc.astimezone(self.ist_tz)

            date = dt_ist.strftime('%A, %d %B, %Y')
            time = dt_ist.strftime('%I:%M %p').lower()
            return date, time
        except Exception as e:
            logger.warning(f"Error converting timestamp {timestamp}: {e}")
            return "Unknown", "Unknown"

    def _parse_news_item(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            news = entry['news_obj']
            date, time = self._convert_timestamp(news['created_at'])

            return {
                'id': uuid.uuid4().hex,
                'title': news.get('title', ''),
                'imageUrl': news.get('image_url', ''),
                'url': news.get('shortened_url', ''),
                'content': news.get('content', ''),
                'author': news.get('author_name', ''),
                'date': date,
                'time': time,
                'readMoreUrl': news.get('source_url', '')
            }
        except KeyError as e:
            logger.warning(f"Missing key in news entry: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing news entry: {e}")
            return None

    async def _fetch_news_data(self, category: str, max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Optional[
        List[Dict]]:
        url = self._build_url(category)
        params = self._build_params(category, max_limit)

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('news_list', [])
                else:
                    logger.error(f"HTTP {response.status}: {await response.text()}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching news for category: {category}")
            return None
        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            return None

    async def get_news(self, category: str, max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Dict[str, Any]:
        news_dictionary = {
            'success': True,
            'category': category,
            'data': []
        }

        news_data = await self._fetch_news_data(category, max_limit)

        if not news_data:
            news_dictionary.update({
                'success': False,
                'error': 'Failed to fetch news data or invalid category'
            })
            return news_dictionary

        tasks = [asyncio.create_task(asyncio.to_thread(self._parse_news_item, entry))
                 for entry in news_data]

        parsed_items = await asyncio.gather(*tasks, return_exceptions=True)

        for item in parsed_items:
            if isinstance(item, dict) and item is not None:
                news_dictionary['data'].append(item)
            elif isinstance(item, Exception):
                logger.warning(f"Error parsing news item: {item}")

        return news_dictionary

    async def get_multiple_categories(self, categories: List[str], max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> \
    Dict[str, Dict[str, Any]]:
        semaphore = asyncio.Semaphore(NewsConfig.MAX_CONCURRENT_REQUESTS)

        async def fetch_category(category: str) -> tuple[str, Dict[str, Any]]:
            async with semaphore:
                result = await self.get_news(category, max_limit)
                return category, result

        tasks = [fetch_category(category) for category in categories]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        category_results = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                category, news_data = result
                category_results[category] = news_data
            elif isinstance(result, Exception):
                logger.error(f"Error fetching category: {result}")

        return category_results


async def get_news_async(category: str, max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Dict[str, Any]:
    async with AsyncNewsAPI() as api:
        return await api.get_news(category, max_limit)


async def get_multiple_news_async(categories: List[str], max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Dict[
    str, Dict[str, Any]]:
    async with AsyncNewsAPI() as api:
        return await api.get_multiple_categories(categories, max_limit)


def getNews(category: str, max_limit: int = NewsConfig.DEFAULT_MAX_LIMIT) -> Dict[str, Any]:
    return asyncio.run(get_news_async(category, max_limit))

