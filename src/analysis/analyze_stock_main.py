import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.get_stock_info import extract_symbol_info
from db_utils.pg_services import save_support_output_to_db
from analysis.analyze_stock import stock_agent, SupportDependencies, DataCrawl
import datetime
import re
from db_utils.pg_pool import init_db_pool

async def main(symbol: str):
    await init_db_pool()
    # 1. Lấy thông tin chứng khoán
    stock_data = await extract_symbol_info(symbol)
    print(f"Stock data for {symbol}: {stock_data}")

    # 2. Phân tích dữ liệu (truyền data đã crawl)
    deps = SupportDependencies(stock_data=DataCrawl(stock_data))
    result = await stock_agent.run(f'Analyze the stock trend for {symbol} in Vietnamese', deps=deps)
    print(f"Analysis: {result.output}")

    # 3. Lưu kết quả phân tích ra audio
    os.makedirs('output/audios', exist_ok=True)
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    audio_path = f'output/audios/{symbol}_analysis_{now}.mp3'
    # Loại bỏ ký tự đặc biệt khỏi text
    text = str(result.output.analysis_advice)
    text = re.sub(r'[\*\/_#\-]+', ' ', text)
    from gtts import gTTS
    tts = gTTS(text, lang='vi')
    tts.save(audio_path)
    print(f"Audio saved to {audio_path}")

    # 4. Lưu kết quả phân tích vào database
    await save_support_output_to_db(result.output)

if __name__ == "__main__":
    asyncio.run(main("FPT"))
