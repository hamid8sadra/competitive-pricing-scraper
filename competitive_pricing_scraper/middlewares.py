# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class CompetitivePricingScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CompetitivePricingScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

# New Added
# competitive_pricing_scraper/middlewares.py
import requests
import random
from bs4 import BeautifulSoup
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

class ProxyMiddleware:
    def __init__(self):
        self.proxies = self._fetch_proxies()
        self.max_retries = 5

    def _fetch_proxies(self):
        try:
            url = 'https://www.sslproxies.org/'
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            proxies = []
            for row in soup.select('table.table tbody tr')[:10]:
                ip = row.select_one('td:nth-child(1)').text
                port = row.select_one('td:nth-child(2)').text
                proxies.append(f'http://{ip}:{port}')
            return proxies if proxies else []
        except Exception as e:
            return []

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
            spider.logger.info(f'Using proxy: {proxy}')
        return None

    def process_response(self, request, response, spider):
        if response.status in [403, 429, 503]:
            spider.logger.warning(f'Retrying due to {response.status} with proxy {request.meta.get("proxy")}')
            return request
        return response

class CustomRetryMiddleware(RetryMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 5)

    def process_exception(self, request, exception, spider):
        if request.meta.get('retry_times', 0) < self.max_retry_times:
            spider.logger.warning(f'Retrying due to {exception} with proxy {request.meta.get("proxy")}')
            return self._retry(request, exception, spider)
        return None