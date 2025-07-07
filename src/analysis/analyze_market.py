from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MarketAnalysisOutput(BaseModel):
  title: str = Field(description="Tiêu đề: Thị trường chứng khoán Việt Nam ngày hôm nay")
  analysis: str = Field(description="Bài phân tích toàn thị trường chứng khoán Việt Nam")
  sentiment: str = Field(description="Sentiment of the market: POSITIVE, NEGATIVE, NEUTRAL")

model = OpenAIModel(
  'deepseek-chat',
  provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY'))
)

SYSTEM_PROMPT = (
    'You are a stock analysis agent in our system. Provide the customer with a stock analysis based on the given stock data. '
    'Do not use any special characters (such as *, /, -, _, #, etc.) or markdown formatting in your output. '
    'Write the analysis in plain, natural Vietnamese sentences only.'
  )

market_agent = Agent(
    model,
    output_type=MarketAnalysisOutput,
    system_prompt=SYSTEM_PROMPT,
)