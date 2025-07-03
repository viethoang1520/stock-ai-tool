from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
import os
import asyncio

DB_CONFIG = {
    'user': 'swd_stockintel_user',
    'password': '04e2ERorKhHYJBHjvEC9poakSgcGYW1F',
    'database': 'swd_stockintel_mmm0',
    'host': 'dpg-d1fqcrili9vc739rk3ug-a.singapore-postgres.render.com',
}

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

# Agent 1: LLM to determine intent and extract stock symbol
intent_model = OpenAIModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY'))
)
intent_agent = Agent(
    intent_model,
    system_prompt=(
        'You are an stock  AI assistant. If the user asks about a stock symbol, return only the symbol (do not add anything else). '
        'If not, return "OTHER".'
    )
)

# Agent 3: LLM to answer other questions
qa_model = OpenAIModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY'))
)
qa_agent = Agent(
    qa_model,
    system_prompt='You are a stock AI assistant. Answer naturally, briefly, and in a friendly manner.'
)

async def get_stock_info(symbol: str):
    conn = await asyncpg.connect(**DB_CONFIG)
    stock_id = await conn.fetchrow('SELECT stock_id FROM stock WHERE symbol=$1', symbol)
    row = await conn.fetchrow('SELECT * FROM post WHERE stock_id=$1', stock_id['stock_id'])
    await conn.close()
    return dict(row) if row else None

@app.post("/chat")
async def chat(req: ChatRequest):
    # Agent 1: LLM determines intent/symbol
    intent = (await intent_agent.run(req.message)).output.strip()
    if intent != "OTHER":
        info = await get_stock_info(intent)
        if info:
            return {"answer": f"Information about {intent}: {info['content']}"}
        else:
            return {"answer": f"No information found for symbol {intent}."}
    # Agent 3: LLM answers other questions
    answer = (await qa_agent.run(req.message)).output
    return {"answer": answer} 