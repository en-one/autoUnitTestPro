import logging
import requests
from typing import Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from config import settings
import constants

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
        
        try:
            if model_type == "openai" and self.openai_client:
                return self._call_openai(prompt)
            elif model_type == "anthropic" and self.anthropic_client:
                return self._call_anthropic(prompt)
            elif model_type == "siliconflow" and self.siliconflow_client:
                return self._call_siliconflow(prompt)
            else:
                available_models = []
                if self.openai_client:
                    available_models.append("openai")
                if self.anthropic_client:
                    available_models.append("anthropic")
                if self.siliconflow_client:
                    available_models.append("siliconflow")
                
                error_msg = f"未配置有效的{model_type}客户端。可用的模型: {', '.join(available_models)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            self.logger.error(f"LLM调用失败: {str(e)}")
            # 不抛出异常，返回空字符串，让调用者处理
            return ""

    def _create_prompt(self, code: str, function_name: str) -> str:
        """
        创建生成测试的提示
        :param code: Go函数代码
        :param function_name: 函数名
        :return: 提示字符串
        """
        return constants.LLM_SUPPPLY_ARGS_PROMPT.format(
            code=code,
            function_name=function_name
        )

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
            # 不抛出异常，返回空字符串
            return ""

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
            # 不抛出异常，返回空字符串
            return ""

    def _call_siliconflow(self, prompt: str) -> str:
        """
        调用硅基流动模型（流式）
        :param prompt: 提示
        :return: 生成的文本
        """
        import json
        try:
            self.logger.debug(f"硅基流动模型: {settings.siliconflow_model}")
            self.logger.debug(f"硅基流动API URL: {settings.siliconflow_url}")
            payload = {
                "model": settings.siliconflow_model,
                "messages": [
                    {"role": "system", "content": "你是一名资深的Go开发工程师，擅长编写单元测试。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4096,
                "stream": True  # 启用流式响应
            }
            self.logger.debug(f"硅基流动请求参数: {payload}")
            response = self.siliconflow_client.post(settings.siliconflow_url, json=payload, stream=True)
            self.logger.debug(f"硅基流动响应状态码: {response.status_code}")
            self.logger.debug(f"硅基流动响应头: {response.headers}")

            full_response = ""
            # 处理流式响应
            for chunk in response.iter_lines():
                if chunk:
                    chunk_data = chunk.decode('utf-8')
                    self.logger.debug(f"硅基流动响应块: {chunk_data}")
                      
                    # 处理数据块
                    if chunk_data.startswith('data: '):
                        chunk_data = chunk_data[6:]
                        if chunk_data == '[DONE]':
                            break
                        try:
                            chunk_json = json.loads(chunk_data)
                            if chunk_json.get('choices') and len(chunk_json['choices']) > 0:
                                delta = chunk_json['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    full_response += delta['content']
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析硅基流动响应块失败: {str(e)}")
            
            self.logger.debug(f"硅基流动完整响应: {full_response}")
            return full_response
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"硅基流动HTTP错误: {str(e)}")
            if 'response' in locals():
                self.logger.error(f"响应内容: {response.text}")
            # 不抛出异常，返回空字符串
            return ""
        except Exception as e:
            self.logger.error(f"硅基流动调用失败: {str(e)}", exc_info=True)
            # 不抛出异常，返回空字符串
            return ""