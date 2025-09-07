from .llm import LLMClient
from config import settings
import logging
# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_siliconflow():
    # 创建LLMClient实例
    llm_client = LLMClient()
    
    # 测试硅基流动调用
    prompt = "你好，硅基流动！"
    print("开始调用硅基流动...")
    try:
        response = llm_client._call_siliconflow(prompt)
        print("调用完成，响应内容:")
        print(response)
    except Exception as e:
        print(f"硅基流动调用失败: {str(e)}")
        logging.error(f"硅基流动调用失败: {str(e)}", exc_info=True)
    
    print('\n测试完成!')

if __name__ == "__main__":
    test_siliconflow()