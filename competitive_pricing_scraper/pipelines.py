# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class CompetitivePricingScraperPipeline:
    def process_item(self, item, spider):
        return item

# New
# competitive_pricing_scraper/pipelines.py
import psycopg2
from scrapy.exceptions import DropItem

class PostgresPipeline:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        db_config = {
            'dbname': crawler.settings.get('DB_NAME', 'pricing_db'),
            'user': crawler.settings.get('DB_USER', 'postgres'),
            'password': crawler.settings.get('DB_PASSWORD', '1234'),
            'host': crawler.settings.get('DB_HOST', 'localhost'),
            'port': crawler.settings.get('DB_PORT', '5432'),
        }
        return cls(db_config)

    def open_spider(self, spider):
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            spider.logger.info("Connected to PostgreSQL database")
        except Exception as e:
            spider.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            spider.logger.info("Disconnected from PostgreSQL database")

    def process_item(self, item, spider):
        try:
            price = float(item['price'].replace('£', '').replace('$', '').strip())
            query = """
                INSERT INTO products (name, price, availability, url, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE
                SET name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    availability = EXCLUDED.availability,
                    timestamp = EXCLUDED.timestamp;
            """
            self.cursor.execute(query, (
                item['name'], price, item['availability'], item['url'], item['timestamp']
            ))
            self.connection.commit()
            spider.logger.info(f"Stored item in PostgreSQL: {item['name']}")
            return item
        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"Error storing item {item['name']}: {e}")
            raise DropItem(f"Failed to store item: {e}")