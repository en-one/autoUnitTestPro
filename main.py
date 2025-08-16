import logging
import argparse
from test_generator import TestGenerator
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='自动生成Go单元测试')
    parser.add_argument('--project-path', type=str, help='Go项目路径')
    parser.add_argument('--model-type', type=str, choices=['openai', 'anthropic', 'siliconflow'], default='openai', help='大模型类型')
    args = parser.parse_args()
    
    print("开始自动生成Go单元测试...")
    
    try:
        generator = TestGenerator()
        results = generator.generate_tests_for_project(args.project_path, args.model_type)
        
        # 打印结果统计
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        
        print(f"\n测试生成完成!")
        print(f"成功生成: {success_count}")
        print(f"生成失败: {failed_count}")
        
        if failed_count > 0:
            print("\n失败的函数:")
            for r in results:
                if r['status'] == 'failed':
                    print(f"- {r['function_name']} ({r['file_path']}): {r['error']}")
    except Exception as e:
        print(f"生成测试时发生错误: {str(e)}")
        logging.error(f"生成测试时发生错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
