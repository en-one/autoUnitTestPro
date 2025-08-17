import os
import subprocess
import sys
from config import settings

def test_generate_test_for_file_all_functions():
    """测试为单个文件中所有函数生成测试用例"""
    print("开始测试为单个文件中所有函数生成测试用例...")

    # 确保项目路径存在
    project_path = settings.go_project_path
    if not os.path.exists(project_path):
        print(f"错误: 项目路径不存在: {project_path}")
        print("提示: 请检查config.py中的go_project_path配置是否正确")
        return False

    # 查找一个有效的Go文件作为测试目标
    # 这里假设在项目的services目录下有Go文件
    services_path = os.path.join(project_path, settings.services_dir)
    if not os.path.exists(services_path):
        print(f"错误: services目录不存在: {services_path}")
        print(f"提示: 请确保项目路径{project_path}下存在{settings.services_dir}目录，并且该目录下包含Go文件")
        return False

    # 查找第一个Go文件
    target_file = None
    go_files_count = 0
    for root, _, files in os.walk(services_path):
        for file in files:
            if file.endswith('.go') and not file.endswith('_test.go'):
                go_files_count += 1
                if not target_file:
                    target_file = os.path.join(root, file)

    if go_files_count == 0:
        print(f"错误: 在{services_path}中未找到Go文件")
        print("提示: 请确保services目录下包含.go文件")
        return False

    print(f"找到{go_files_count}个Go文件，使用第一个文件: {target_file}")

    # 检查是否有权限访问该文件
    try:
        with open(target_file, 'r') as f:
            pass
    except PermissionError:
        print(f"错误: 没有权限访问文件: {target_file}")
        print("提示: 请确保程序有权限访问该文件")
        return False
    except Exception as e:
        print(f"错误: 无法访问文件{target_file}: {str(e)}")
        return False

    # 测试不使用LLM的情况
    print("测试不使用LLM为文件中所有函数生成测试用例...")
    cmd_no_llm = [
        sys.executable,
        'main.py',
        '--file-path', target_file,
        '--all-functions',
        '--no-llm'
    ]
    result_no_llm = subprocess.run(cmd_no_llm, cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
    print(f"命令输出: {result_no_llm.stdout}")
    if result_no_llm.returncode != 0:
        print(f"错误: 命令执行失败: {result_no_llm.stderr}")
        return False

    # 测试使用LLM的情况
    print("测试使用LLM为文件中所有函数生成测试用例...")
    cmd_with_llm = [
        sys.executable,
        'main.py',
        '--file-path', target_file,
        '--all-functions'
    ]
    result_with_llm = subprocess.run(cmd_with_llm, cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
    print(f"命令输出: {result_with_llm.stdout}")
    if result_with_llm.returncode != 0:
        print(f"错误: 命令执行失败: {result_with_llm.stderr}")
        return False

    print("测试完成！")
    return True

if __name__ == "__main__":
    success = test_generate_test_for_file_all_functions()
    if success:
        print("所有测试通过！")
        sys.exit(0)
    else:
        print("测试失败！")
        sys.exit(1)