import logging
import argparse
from generator import TestTemplateGenerator
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='自动生成Go单元测试')
    parser.add_argument('--project-path', type=str, help='Go项目路径')
    parser.add_argument('--file-path', type=str, help='包含要测试函数的文件路径')
    parser.add_argument('--function-name', type=str, help='要生成测试的函数名')
    parser.add_argument('--all-functions', action='store_true', help='为文件中的所有函数生成测试用例（与--file-path配合使用）')
    parser.add_argument('--no-llm', action='store_true', help='不使用LLM补充测试用例参数')
    args = parser.parse_args()
    
    print("开始自动生成Go单元测试...")
    
    try:
        generator = TestTemplateGenerator()
        if args.file_path and args.all_functions:
            use_llm = not args.no_llm
            results = generator.generate_test_templates_for_file(args.file_path, use_llm)
        elif args.file_path and args.function_name:
            use_llm = not args.no_llm
            results = [generator.generate_test_template_for_single_function(args.file_path, args.function_name, use_llm)]
        else:
            use_llm = not args.no_llm
            results = generator.generate_test_templates_for_project(args.project_path, use_llm)
        
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
