from db_utils.pg_pool import get_pool
from datetime import datetime, time

async def save_support_output_to_db(support_output, session):
    """
    Lưu thông tin SupportOutput vào bảng stock_analysis, kèm phiên giao dịch.
    support_output: object có các thuộc tính analysis_advice, symbol, sentiment, topic
    session: 'morning', 'afternoon', hoặc 'out_of_session'
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        # Lấy stock_id từ bảng stock
        stock_id = await conn.fetchrow("SELECT stock_id FROM stock WHERE symbol = $1", support_output.symbol)
        if not stock_id:
            raise ValueError(f"Stock with symbol {support_output.symbol} not found")
        
        stock_id = stock_id["stock_id"]
        
        # Lấy session từ hàm get_trading_session
        session = get_trading_session()

        # Lưu thông tin vào bảng post
        await conn.execute(
            """
            INSERT INTO post (content, stock_id, sentiment, topic, session, level)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            support_output.analysis_advice,
            stock_id,
            support_output.sentiment,
            support_output.topic,
            session,
            "SYMBOL"
        )

def get_trading_session(dt=None):
    if dt is None:
        dt = datetime.now()
    t = dt.time()
    if t < time(15, 0):
      return "MORNING"
    elif time(15, 0) <= t < time(17, 0):
      return "AFTERNOON"
    else:
      return "ALLDAY"

async def save_market_analysis_to_db(market_analysis):
  """
  Lưu thông tin MarketAnalysis vào bảng post
  market_analysis: object có các thuộc tính analysis, sentiment
  """
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO post (content, sentiment, topic, level)
            VALUES ($1, $2, $3, $4)
            """,
            market_analysis.analysis,
            market_analysis.sentiment,
            "MARKET",
            "MARKET"
        )


# Ví dụ sử dụng:
session = get_trading_session()
print(f"Phiên hiện tại: {session}")
