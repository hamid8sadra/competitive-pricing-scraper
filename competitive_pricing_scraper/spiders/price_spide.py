# competitive_pricing_scraper/spiders/price_spide.py
import scrapy
from competitive_pricing_scraper.items import ProductItem
from datetime import datetime

class PriceSpide(scrapy.Spider):
    name = 'price_spide'
    allowed_domains = ['books.toscrape.com']
    start_urls = ['http://books.toscrape.com/']

    def parse(self, response):
        products = response.css('.product_pod')
        for product in products:
            item = ProductItem()
            item['name'] = product.css('h3 a::attr(title)').get(default='N/A')
            item['price'] = product.css('.price_color::text').get(default='0.00')
            item['availability'] = product.css('.availability::text').get(default='Unknown').strip()
            item['url'] = response.urljoin(product.css('h3 a::attr(href)').get())
            item['timestamp'] = datetime.utcnow().isoformat()
            yield item
        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)