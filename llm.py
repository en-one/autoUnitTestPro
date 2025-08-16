import logging
import requests
from typing import Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from config import settings

class LLMClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self.anthropic_client = None
        self.siliconflow_client = None
        
        # 初始化客户端
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        
        if settings.siliconflow_api_key:
            self.siliconflow_client = requests.Session()
            self.siliconflow_client.headers.update({
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json"
            })

    def generate_test(self, code: str, function_name: str, model_type: str = "openai") -> str:
        """
        生成Go单元测试代码
        :param code: Go函数代码
        :param function_name: 函数名
        :param model_type: 模型类型 (openai, anthropic 或 siliconflow)
        :return: 生成的测试代码
        """
        prompt = self._create_prompt(code, function_name)
        
        if model_type == "openai" and self.openai_client:
            return self._call_openai(prompt)
        elif model_type == "anthropic" and self.anthropic_client:
            return self._call_anthropic(prompt)
        elif model_type == "siliconflow" and self.siliconflow_client:
            return self._call_siliconflow(prompt)
        else:
            self.logger.error(f"未配置有效的{model_type}客户端")
            raise ValueError(f"未配置有效的{model_type}客户端")

    def _create_prompt(self, code: str, function_name: str) -> str:
        """
        创建生成测试的提示
        :param code: Go函数代码
        :param function_name: 函数名
        :return: 提示字符串
        """
        return f"""
请为以下Go函数编写单元测试,使用表格驱动测试方式,包含至少一个正例和一个反例。
测试框架使用标准库`testing`和`gomock`。

函数代码:
{code}

函数名: {function_name}

测试代码要求:
1. 导入必要的包
2. 包含TestMain函数(如果不存在)
3. 为每个函数创建测试函数，使用表格驱动测试
4. 包含正例和反例测试
5. 模拟依赖项
6. 断言结果正确性
"""

    def _call_openai(self, prompt: str) -> str:
        """
        调用OpenAI模型
        :param prompt: 提示
        :return: 生成的文本
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是一名资深的Go开发工程师，擅长编写单元测试。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI调用失败: {str(e)}")
            raise

    def _call_anthropic(self, prompt: str) -> str:
        """
        调用Anthropic模型
        :param prompt: 提示
        :return: 生成的文本
        """
        try:
            response = self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=4096,
                system="你是一名资深的Go开发工程师，擅长编写单元测试。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic调用失败: {str(e)}")
            raise

    def _call_siliconflow(self, prompt: str) -> str:
        """
        调用硅基流动模型
        :param prompt: 提示
        :return: 生成的文本
        """
        try:
            payload = {
                "model": settings.siliconflow_model,
                "messages": [
                    {"role": "system", "content": "你是一名资深的Go开发工程师，擅长编写单元测试。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4096
            }
            response = self.siliconflow_client.post(settings.siliconflow_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"硅基流动调用失败: {str(e)}")
            raise