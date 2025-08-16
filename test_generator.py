import os
import logging
from typing import List, Dict, Any
from code_analyzer import GoCodeAnalyzer
from llm import LLMClient
from config import settings

class TestGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = GoCodeAnalyzer()
        self.llm_client = LLMClient()

    def generate_tests_for_project(self, project_path: str = None) -> List[Dict[str, Any]]:
        """
        为整个项目生成单元测试
        :param project_path: 项目路径，默认为配置文件中的路径
        :return: 生成的测试信息列表
        """
        if not project_path:
            project_path = settings.go_project_path
            
        if not os.path.exists(project_path):
            self.logger.error(f"项目路径不存在: {project_path}")
            raise ValueError(f"项目路径不存在: {project_path}")
        
        # 分析services目录下的代码
        services_path = os.path.join(project_path, settings.services_dir)
        if not os.path.exists(services_path):
            self.logger.error(f"services目录不存在: {services_path}")
            raise ValueError(f"services目录不存在: {services_path}")
        
        # 分析代码
        functions = self.code_analyzer.analyze_directory(services_path)
        self.logger.info(f"找到{len(functions)}个函数需要生成测试")
        
        # 为每个函数生成测试
        results = []
        for func in functions:
            try:
                test_code = self.generate_test_for_function(func)
                # 保存测试代码
                test_file_path = self._get_test_file_path(func['file_path'])
                self._save_test_file(test_file_path, test_code, func['name'])
                
                results.append({
                    'function_name': func['name'],
                    'file_path': func['file_path'],
                    'test_file_path': test_file_path,
                    'status': 'success'
                })
            except Exception as e:
                self.logger.error(f"为函数{func['name']}生成测试失败: {str(e)}")
                results.append({
                    'function_name': func['name'],
                    'file_path': func['file_path'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results

    def generate_test_for_function(self, func_info: Dict[str, Any], model_type: str = "openai") -> str:
        """
        为单个函数生成测试
        :param func_info: 函数信息
        :param model_type: 模型类型
        :return: 生成的测试代码
        """
        return self.llm_client.generate_test(
            code=func_info['full_code'],
            function_name=func_info['name'],
            model_type=model_type
        )

    def _get_test_file_path(self, source_file_path: str) -> str:
        """
        获取测试文件路径
        :param source_file_path: 源文件路径
        :return: 测试文件路径
        """
        dir_name, file_name = os.path.split(source_file_path)
        base_name = os.path.splitext(file_name)[0]
        return os.path.join(dir_name, f"{base_name}_test.go")

    def _save_test_file(self, test_file_path: str, test_code: str, function_name: str) -> None:
        """
        保存测试文件
        :param test_file_path: 测试文件路径
        :param test_code: 测试代码
        :param function_name: 函数名
        """
        # 检查文件是否存在
        if os.path.exists(test_file_path):
            # 文件存在，检查是否已有该函数的测试
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否已有TestMain函数
            has_test_main = 'func TestMain(' in content
            # 检查是否已有该函数的测试
            test_func_name = f"Test{function_name}"
            has_test_func = f"func {test_func_name}(" in content
            
            if has_test_func:
                self.logger.warning(f"函数{function_name}的测试已存在于{test_file_path}")
                return
            
            # 如果没有TestMain函数，添加到文件开头
            if not has_test_main:
                test_main_code = self._generate_test_main()
                content = test_main_code + '\n\n' + content
            
            # 添加新的测试函数
            content += '\n\n' + test_code
        else:
            # 文件不存在，创建新文件
            content = self._generate_test_main() + '\n\n' + test_code
        
        # 保存文件
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"已保存测试文件到{test_file_path}")

    def _generate_test_main(self) -> str:
        """
        生成TestMain函数
        :return: TestMain函数代码
        """
        return """package main

import (
    "fmt"
    "testing"
    "git.shining3d.com/cloud/dental/unit"
)

func TestMain(m *testing.M) {
    fmt.Println("TestBegin")
    unit.InitTestConfig()

    p := unit.InitGlobalMonkeyPatch()
    defer func() {
        p.Reset()
    }()

    m.Run()
    fmt.Println("TestEnd")
}
"""