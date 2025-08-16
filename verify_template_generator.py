#!/usr/bin/env python3
import os
import sys
import subprocess
from test_generator import TestTemplateGenerator

def verify_generator():
    """验证测试用例模板生成器的所有功能是否正常"""
    print("开始验证测试用例模板生成器...")
    
    # 测试1: 验证类和方法重命名
    try:
        generator = TestTemplateGenerator()
        print("测试1通过: 成功初始化TestTemplateGenerator类")
    except Exception as e:
        print(f"测试1失败: 无法初始化TestTemplateGenerator类: {str(e)}")
        return False
    
    # 测试2: 创建临时测试文件
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_temp")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "calculator.go")
    
    with open(test_file, "w") as f:
        f.write("""package verify_temp

func Add(a, b int) int {
    return a + b
}

func Subtract(a, b int) int {
    return a - b
}
""")
    
    # 测试3: 为单个函数生成测试模板
    try:
        result = generator.generate_test_template_for_single_function(test_file, "Add")
        if result['status'] == 'success':
            print(f"测试3通过: 成功为Add函数生成测试模板")
        else:
            print(f"测试3失败: 为Add函数生成测试模板失败: {result.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"测试3失败: 调用generate_test_template_for_single_function方法时出错: {str(e)}")
        return False
    
    # 测试4: 为项目生成测试模板
    try:
        results = generator.generate_test_templates_for_project(test_dir)
        success_count = sum(1 for r in results if r['status'] == 'success')
        if success_count >= 1:
            print(f"测试4通过: 成功为项目生成测试模板，成功数量: {success_count}")
        else:
            print(f"测试4失败: 为项目生成测试模板失败")
            return False
    except Exception as e:
        print(f"测试4失败: 调用generate_test_templates_for_project方法时出错: {str(e)}")
        return False
    
    # 测试5: 验证main.py是否能正常工作
    try:
        cmd = ["uv", "run", "python", "main.py", "--file-path", test_file, "--function-name", "Subtract"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("测试5通过: main.py能够正常工作")
        else:
            print(f"测试5失败: main.py运行失败，错误输出: {result.stderr}")
            return False
    except Exception as e:
        print(f"测试5失败: 运行main.py时出错: {str(e)}")
        return False
    
    print("所有测试通过! 测试用例模板生成器已成功更新")
    return True

def cleanup(test_dir):
    """清理测试文件"""
    if os.path.exists(os.path.join(test_dir, "calculator_test.go")):
        os.remove(os.path.join(test_dir, "calculator_test.go"))
    if os.path.exists(os.path.join(test_dir, "calculator.go")):
        os.remove(os.path.join(test_dir, "calculator.go"))
    if os.path.exists(test_dir) and not os.listdir(test_dir):
        os.rmdir(test_dir)

if __name__ == "__main__":
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_temp")
    try:
        success = verify_generator()
        sys.exit(0 if success else 1)
    finally:
        cleanup(test_dir)


# 运行方式:
# uv run python verify_template_generator.py