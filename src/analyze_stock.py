from dataclasses import dataclass

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from get_stock_info import extract_symbol_info

class DataCrawl:
  @classmethod
  async def stock_analysis(cls, *, symbol: str ) -> str:
    data = await extract_symbol_info(symbol=symbol)
    return data
  
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
    'You are a stock analysis agent in our system, give the'
    'customer stock analysis on the given stock data'
  )
)

@stock_agent.system_prompt
async def add_analysis_data(ctx: RunContext[SupportDependencies]) -> str:
  data = await ctx.deps.stock_data.stock_analysis(symbol='ACB')
  return f"The stock data is {data}"


if __name__ == '__main__':
  deps = SupportDependencies(stock_data=DataCrawl())
  result = stock_agent.run_sync('Analyze the stock trend', deps=deps)
  print(result.output)