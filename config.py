from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    # Anthropic配置
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    
    # 硅基流动配置
    siliconflow_api_key: Optional[str] = None
    siliconflow_model: str = "deepseek-ai/deepseek-chat"
    siliconflow_url: str = "https://api.siliconflow.cn/v1/chat/completions"
    
    # 项目配置
    go_project_path: str = "/Users/zhangliyu/Documents/code/clouddental"
    services_dir: str = "services"
    test_template_dir: str = "templates"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()