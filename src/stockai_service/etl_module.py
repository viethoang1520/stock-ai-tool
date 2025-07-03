import asyncio
from get_stock_info import extract_symbol_info
from analyze_stock import stock_agent, SupportDependencies, DataCrawl
import asyncpg
import datetime
import os

DB_CONFIG = {
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_db',
    'host': 'localhost',
}

async def save_to_db(symbol, data, analysis):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute('''
        INSERT INTO stocks(symbol, data, analysis, created_at)
        VALUES($1, $2, $3, $4)
        ON CONFLICT(symbol) DO UPDATE SET data=$2, analysis=$3, created_at=$4
    ''', symbol, data, analysis, datetime.datetime.now())
    await conn.close()

async def etl(symbol: str):
    # Crawl
    stock_data = await extract_symbol_info(symbol)
    # Phân tích
    deps = SupportDependencies(stock_data=DataCrawl(stock_data))
    result = await stock_agent.run(f'Analyze the stock trend for {symbol} in English', deps=deps)
    analysis = str(result.output)
    # Lưu DB
    await save_to_db(symbol, stock_data, analysis)
    print(f"Đã lưu {symbol} vào DB với phân tích: {analysis}")

if __name__ == "__main__":
    symbols = ["FPT", "VNM", "VCB"]  # Thay bằng danh sách mã bạn muốn crawl
    asyncio.run(asyncio.gather(*(etl(symbol) for symbol in symbols))) 