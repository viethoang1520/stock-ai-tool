from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MarketAnalysisOutput(BaseModel):
    analysis: str = Field(description="Bài phân tích toàn thị trường chứng khoán Việt Nam")
    sentiment: str = Field(description="Sentiment of the market: POSITIVE, NEGATIVE, NEUTRAL")

model = OpenAIModel(
  'deepseek-chat',
  provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY'))
)

SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích chứng khoán. Hãy viết một bài phân tích cấp độ thị trường chứng khoán Việt Nam dựa trên các tiêu đề tin tức sau, tập trung vào xu hướng, rủi ro, cơ hội nổi bật và tác động đến thị trường. Bài viết cần sâu sắc, có dẫn chứng từ tiêu đề, và mang tính tổng hợp, không liệt kê từng tin."
)

market_agent = Agent(
    model,
    output_type=MarketAnalysisOutput,
    system_prompt=SYSTEM_PROMPT,
)