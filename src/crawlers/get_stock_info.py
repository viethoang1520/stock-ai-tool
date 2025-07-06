from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawlers.get_stock_page_uri import get_stock_page_uri
import json
import pyttsx3
import os

stock_code = "FPT"


async def extract_symbol_info(symbol:str):
  browser_config = BrowserConfig(
    browser_type="chromium",
    verbose=True,
    headless=False
  )
  crawler_config = CrawlerRunConfig(
    extraction_strategy=JsonCssExtractionStrategy(
      schema={
        "name": "Symbol Info",
        "baseSelector": ".dl-thongtin",
        "fields": [
          {
            "name": "reference_price",
            "selector": "#price__ref",
            "type": "text"
          },
          {
            "name": "ceiling_price",
            "selector": "#price__ceiling",
            "type": "text"
          },
          {
            "name": "floor_price",
            "selector": "#price__floor",
            "type": "text"
          },
          {
            "name": "highest_price",
            "selector": "#price__high",
            "type": "text"
          },
          {
            "name": "lowest_price",
            "selector": "#price__low",
            "type": "text"
          },
          {
            "name": "foreign_volume",
            "selector": "#foregin__buyvol",
            "type": "text"
          },
          {
            "name": "foreign_buy_value",
            "selector": "#foregin__buyval",
            "type": "text"
          },
          {
            "name": "foreign_sell_value",
            "selector": "#foregin__sellval",
            "type": "text"
          },
          {
            "name": "foreign_remaining_room",
            "selector": "#foregin__room",
            "type": "text"
          },
          {
            "name": "basic_EPS",
            "selector": ".dlt-left-half #ContentPlaceHolder1_ucTradeInfoV3_pnEPS .r ",
            "type": "text"
          },
          {
            "name": "diluted_EPS",
            "selector": "#ContentPlaceHolder1_ucTradeInfoV3_liEPSDieuChinh .r ",
            "type": "text"
          },
          {
            "name": "P/E",
            "selector": "#ContentPlaceHolder1_ucTradeInfoV3_pnEPS li.clearfix:nth-of-type(3) .r",
            "type": "text"
          },
          {
            "name": "book_value_per_share",
            "selector": ".dlt-left-half .dltl-other > ul > li.clearfix .r",
            "type": "text"
          },
          {
            "name": "P/B",
            "selector": ".dlt-left-half .dltl-other > ul > li.clearfix:nth-of-type(2) .r",
            "type": "text"
          },         
        ]
      }
    )
  )


  url = await get_stock_page_uri(symbol)

  async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url=url, config=crawler_config)
    
    if result and result.extracted_content:
      data = json.loads(result.extracted_content)
      print(data)
      return data

if __name__ == "__main__":
  import asyncio
  asyncio.run(extract_symbol_info("FPT"))
