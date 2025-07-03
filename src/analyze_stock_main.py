import asyncio
from get_stock_info import extract_symbol_info
from analyze_stock import stock_agent, SupportDependencies, DataCrawl
import pyttsx3
import os
import datetime
import re

async def main(symbol: str):
    # 1. Lấy thông tin chứng khoán
    stock_data = await extract_symbol_info(symbol)
    print(f"Stock data for {symbol}: {stock_data}")

    # 2. Phân tích dữ liệu (truyền data đã crawl)
    deps = SupportDependencies(stock_data=DataCrawl(stock_data))
    result = await stock_agent.run(f'Analyze the stock trend for {symbol} in English', deps=deps)
    print(f"Analysis: {result.output}")

    # 3. Lưu kết quả phân tích ra audio
    os.makedirs('output/audios', exist_ok=True)
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    audio_path = f'output/audios/{symbol}_analysis_{now}.mp3'
    engine = pyttsx3.init()
    # Giảm tốc độ đọc
    rate = engine.getProperty('rate')
    engine.setProperty('rate', int(rate * 0.9))
    # Loại bỏ ký tự đặc biệt khỏi text
    text = str(result.output)
    text = re.sub(r'[\*\/_#\-]+', ' ', text)
    engine.save_to_file(text, audio_path)
    engine.runAndWait()
    print(f"Audio saved to {audio_path}")

if __name__ == "__main__":
    asyncio.run(main("FPT"))
