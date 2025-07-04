from dataclasses import dataclass

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from get_stock_info import extract_symbol_info
import pyttsx3
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
    'Write the analysis in plain, natural English sentences only.'
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
  engine = pyttsx3.init()
  engine.save_to_file(str(result.output), audio_path)
  engine.runAndWait()
  print(f"Audio saved to {audio_path}")