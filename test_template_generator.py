#!/usr/bin/env python3
import os
import sys
from test_generator import TestTemplateGenerator

def test_generator_renaming():
    """测试重命名后的TestTemplateGenerator类功能是否正常"""
    # 创建测试目录和文件
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_temp")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "sample.go")
    
    # 写入测试Go文件
    with open(test_file, "w") as f:
        f.write("""package sample

func Add(a, b int) int {
    return a + b
}
""")
    
    try:
        # 初始化重命名后的生成器
        generator = TestTemplateGenerator()
        
        # 测试单个函数生成测试模板
        result = generator.generate_test_template_for_single_function(test_file, "Add")
        print(f"测试结果: {result}")
        
        # 检查生成的测试文件是否存在
        test_file_path = os.path.join(test_dir, "sample_test.go")
        if os.path.exists(test_file_path):
            print(f"成功生成测试用例模板: {test_file_path}")
            with open(test_file_path, "r") as f:
                content = f.read()
                print(f"测试用例模板内容预览:\n{content[:300]}...")
        else:
            print(f"未生成测试用例模板: {test_file_path}")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        if os.path.exists(test_dir) and not os.listdir(test_dir):
            os.rmdir(test_dir)

if __name__ == "__main__":
    test_generator_renaming()


# 运行方式:
# uv run python test_template_generator.py