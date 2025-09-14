from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    # Anthropic配置
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    
    # 硅基流动配置
    siliconflow_api_key: Optional[str] = None
    siliconflow_model: str = "Pro/deepseek-ai/DeepSeek-R1"
    #  siliconflow_model: str = "Pro/deepseek-ai/DeepSeek-V3.1"
    siliconflow_url: str = "https://api.siliconflow.cn/v1"
    
    # 项目配置
    go_project_path: str = "/Users/zhangliyu/Documents/codellm/autoUnitTestPro"
    services_dir: str = "."
    test_template_dir: str = "templates"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()