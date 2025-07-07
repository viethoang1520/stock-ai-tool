import os
import sys
# Ensure parent directory is in sys.path for module resolution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from typing import List, Dict
import asyncio
import re
from crawlers.crawl_cafebiz_news import extract_cafebiz_news
from analysis.analyze_market import market_agent, MarketAnalysisOutput
from db_utils.pg_services import save_market_analysis_to_db
from db_utils.pg_pool import init_db_pool

async def main():
    await init_db_pool()
    # 1. Crawl dữ liệu
    crawl_results = await extract_cafebiz_news()
    for item in crawl_results:
        url = item.get('url')
        if not item.get('success'):
            print(f"Failed to crawl {url}: {item.get('error_message')}")
            continue
        news = item.get('news', [])
        titles = '\n'.join([n.get('title', '') for n in news if n.get('title')])
        prompt = f"Các tiêu đề tin tức từ {url} về thị trường chứng khoán:\n{titles}\n\nHãy phân tích toàn thị trường như một chuyên gia."
        # 2. Gọi agent
        result = await market_agent.run(prompt)
        print(f"URL: {url}\nAnalysis:\n{result.output.analysis}\n{'-'*40}")
        # 3. Lưu audio
        from gtts import gTTS
        os.makedirs('output/audios', exist_ok=True)
        audio_path = f'output/audios/market_analysis_{os.path.basename(url)}.mp3'
        text = re.sub(r'[\*\/_#\\-]+', ' ', result.output.analysis)
        tts = gTTS(text, lang='vi')
        tts.save(audio_path)
        print(f"Audio saved to {audio_path}")

        # 4. Lưu thông tin vào database
        await save_market_analysis_to_db(result.output)

if __name__ == "__main__":
    asyncio.run(main())
