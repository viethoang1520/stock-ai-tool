from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json

async def extract_cafebiz_news():
    # Initialize browser config
    browser_config = BrowserConfig(browser_type="chromium", headless=False)
    crawler_config = CrawlerRunConfig(
      extraction_strategy=JsonCssExtractionStrategy(
        schema={
          "name": "CafeBiz News",
          "baseSelector": " .cfbiznews_box",
          "fields": [
            {
              "name": "title",
              "selector": "h2 a, h3 a",
              "type": "text"
            },
          ]
        }
      )
    )

    urls=[
        'https://cafebiz.vn/vi-mo.chn',
        'https://cafebiz.vn/cau-chuyen-kinh-doanh.chn',
        'https://cafebiz.vn/cong-nghe.chn'
      ]

    async with AsyncWebCrawler(config=browser_config) as crawler:
      results = await crawler.arun_many(
        urls=urls, config=crawler_config, 
        bypass_cache=True, 
        verbose=True
      )

      output = []
      for result in results:
        if result.success and result.extracted_content:
          news = json.loads(result.extracted_content)
          output.append({
            'url': result.url,
            'success': True,
            'news': news
          })
        else:
          output.append({
            'url': result.url,
            'success': False,
            'error_message': result.error_message
          })
      return output

if __name__ == "__main__":
  import asyncio
  results = asyncio.run(extract_cafebiz_news())
  import pprint
  pprint.pprint(results)


