from dataclasses import dataclass

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from crawlers.get_stock_info import extract_symbol_info
from gtts import gTTS
import os

class DataCrawl:
  def __init__(self, data):
    self.data = data

  async def stock_analysis(self) -> str:
    return self.data
  
@dataclass
class SupportDependencies:
  stock_data: DataCrawl

class SupportOutput(BaseModel):
  analysis_advice: str = Field(description='Advice return to the customer')
  symbol: str = Field(description='Symbol of the stock')
  sentiment: str = Field(description='Sentiment of the stock: POSITIVE, NEGATIVE, NEUTRAL')
  topic: str = Field(description='Topic of the stock: news, financial, etc.')

  
model = OpenAIModel(
  'deepseek-chat',
  provider=DeepSeekProvider(api_key='sk-77f83d2fabc341ae98273eb63c0dd77a')
)

stock_agent = Agent(
  model,
  deps_type=SupportDependencies,
  output_type=SupportOutput,
  system_prompt=(
    'You are a stock analysis agent in our system. Provide the customer with a stock analysis based on the given stock data. '
    'Do not use any special characters (such as *, /, -, _, #, etc.) or markdown formatting in your output. '
    'Write the analysis in plain, natural Vietnamese sentences only.'
  )
)

@stock_agent.system_prompt
async def add_analysis_data(ctx: RunContext[SupportDependencies]) -> str:
  data = await ctx.deps.stock_data.stock_analysis()
  return f"The stock data is {data}"


if __name__ == '__main__':
  import asyncio
  # Ví dụ test với data mẫu
  deps = SupportDependencies(stock_data=DataCrawl({'sample': 'data'}))
  result = asyncio.run(stock_agent.run('Analyze the stock trend', deps=deps))
  print(result.output)
  # Text to Speech cho kết quả phân tích
  os.makedirs('output/audios', exist_ok=True)
  audio_path = 'output/audios/ACB_analysis.mp3'
  tts = gTTS(str(result.output), lang='vi')
  tts.save(audio_path)
  print(f"Audio saved to {audio_path}")