import os
import logging
from typing import List, Dict, Any
from code_analyzer import GoCodeAnalyzer
import constants
from llm import LLMClient
from config import settings

class TestTemplateGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = GoCodeAnalyzer()
        self.llm_client = LLMClient()
        self.logger.info("LLM客户端初始化完成")

    def supplement_test_params_for_existing_template(self, test_file_path: str, function_code: str, function_name: str) -> Dict[str, Any]:
        """
        为已存在的测试模板补充测试用例参数
        :param test_file_path: 测试文件路径
        :param function_code: 函数代码
        :param function_name: 函数名
        :return: 补充参数后的测试模板信息
        """
        if not os.path.exists(test_file_path):
            self.logger.error(f"测试文件不存在: {test_file_path}")
            return {
                'function_name': function_name,
                'test_file_path': test_file_path,
                'status': 'failed',
                'error': f"测试文件不存在: {test_file_path}"
            }

        try:
            # 读取原始测试模板
            with open(test_file_path, 'r', encoding='utf-8') as f:
                original_template = f.read()

            # 调用LLM补充测试参数
            supplemented_test = self._supplement_test_params(function_code, function_name, original_template)

            # 保存补充后的测试文件
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(supplemented_test)

            return {
                'function_name': function_name,
                'test_file_path': test_file_path,
                'status': 'success',
                'message': '测试参数补充成功，已更新测试文件'
            }
        except Exception as e:
            self.logger.error(f"补充测试参数失败: {str(e)}")
            return {
                'function_name': function_name,
                'test_file_path': test_file_path,
                'status': 'failed',
                'error': f"补充测试参数失败: {str(e)}"
            }

    def generate_test_templates_for_project(self, project_path: str = None, use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        为整个项目生成单元测试用例模板
        :param project_path: 项目路径，默认为配置文件中的路径
        :param use_llm: 是否使用LLM补充测试用例参数，默认为True
        :return: 生成的测试模板信息列表
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
                test_template_code = self.generate_test_template_for_function(func, use_llm)
                # 保存测试代码
                test_file_path = self._get_test_file_path(func['file_path'])
                self._save_test_file(test_file_path, test_template_code, func['name'])
                
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

    def generate_test_template_for_function(self, func_info: Dict[str, Any], use_llm: bool = True) -> str:
        """
        为单个函数生成测试用例模板
        :param func_info: 函数信息
        :param use_llm: 是否使用LLM补充测试用例参数，默认为True
        :return: 生成的测试用例模板代码
        """
        function_name = func_info['name']
        file_path = func_info['file_path']
        
        # 确定包名
        target_dir = os.path.dirname(file_path)
        package_name = os.path.basename(target_dir)
        
        # 1. 优先生成基础测试模板
        test_template = constants.TEST_FUNCTION_TEMPLATE.format(
            package_name=package_name,
            function_name=function_name
        )
        
        # 2. 如果启用LLM，则尝试调用LLM补充测试参数
        if use_llm:
            try:
                # 获取函数的完整代码
                function_code = self.code_analyzer.get_function_code(file_path, function_name)
                # 调用LLM补充测试参数
                supplemented_test_template = self._supplement_test_params(function_code, function_name, test_template)
                return supplemented_test_template
            except Exception as e:
                self.logger.error(f"调用LLM补充测试参数失败，使用基础模板: {str(e)}")
                # 失败时返回基础模板
                return test_template
        else:
            self.logger.info(f"未启用LLM，直接返回基础测试模板: 函数名={function_name}")
            return test_template

    def _supplement_test_params(self, function_code: str, function_name: str, test_template: str) -> str:
        """
        调用LLM补充测试用例参数
        :param function_code: 函数代码
        :param function_name: 函数名
        :param test_template: 测试模板
        :return: 补充参数后的测试模板
        """
        try:
            self.logger.info(f"开始调用LLM补充测试参数: 函数名={function_name}")
            # 调用LLM生成补充参数的测试用例
            # 使用硅基流动模型生成测试用例
            supplemented_test = self.llm_client.generate_test(function_code, function_name, model_type="siliconflow")
            
            # 检查返回结果是否为空
            if not supplemented_test.strip():
                self.logger.warning(f"LLM返回空结果，使用基础模板")
                return test_template
            
            self.logger.info(f"LLM调用成功，生成的测试代码长度: {len(supplemented_test)}")
            return supplemented_test
        except Exception as e:
            self.logger.error(f"调用LLM补充测试参数失败: {str(e)}")
            # 失败时返回原始模板
            return test_template

    def _get_test_file_path(self, source_file_path: str) -> str:
        """
        获取测试文件路径
        :param source_file_path: 源文件路径
        :return: 测试文件路径
        """
        dir_name, file_name = os.path.split(source_file_path)
        base_name = os.path.splitext(file_name)[0]
        return os.path.join(dir_name, f"{base_name}_test.go")

    def generate_test_template_for_single_function(self, file_path: str, function_name: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        为单个函数生成单元测试用例模板
        :param file_path: 包含函数的文件路径
        :param function_name: 要生成测试用例模板的函数名
        :param use_llm: 是否使用LLM补充测试用例参数，默认为True
        :return: 生成的测试模板信息
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return {
                'function_name': function_name,
                'file_path': file_path,
                'status': 'failed',
                'error': f"文件不存在: {file_path}"
            }
        
        # 分析指定文件
        try:
            functions = self.code_analyzer.analyze_file(file_path)
        except Exception as e:
            self.logger.error(f"分析文件{file_path}失败: {str(e)}")
            return {
                'function_name': function_name,
                'file_path': file_path,
                'status': 'failed',
                'error': f"分析文件失败: {str(e)}"
            }
        
        # 查找指定函数
        target_func = None
        for func in functions:
            if func['name'] == function_name:
                target_func = func
                break
        
        if not target_func:
            self.logger.error(f"在文件{file_path}中未找到函数{function_name}")
            return {
                'function_name': function_name,
                'file_path': file_path,
                'status': 'failed',
                'error': f"未找到函数{function_name}"
            }
        
        try:
            # 生成测试代码 - 确保即使LLM调用失败也能返回基础模板
            test_template_code = self.generate_test_template_for_function(target_func, use_llm)
            
            # 保存测试代码
            test_file_path = self._get_test_file_path(file_path)
            self._save_test_file(test_file_path, test_template_code, function_name)
            
            return {
                'function_name': function_name,
                'file_path': file_path,
                'test_file_path': test_file_path,
                'status': 'success',
                'message': '测试模板生成成功，已保存到指定路径'
            }
        except Exception as e:
            self.logger.error(f"保存测试文件失败: {str(e)}")
            
            # 尝试直接返回生成的测试模板代码（即使保存失败）
            return {
                'function_name': function_name,
                'file_path': file_path,
                'status': 'partially_failed',
                'error': f"保存测试文件失败: {str(e)}",
                'test_template_code': test_template_code
            }

    def _merge_imports(self, existing_code: str, new_code: str) -> str:
        """
        合并两个代码字符串中的import语句和处理package声明
        :param existing_code: 已存在的代码
        :param new_code: 新的代码
        :return: 合并后的代码
        """
        # 处理package声明
        # 提取现有代码中的package声明
        existing_package_line = ''
        existing_lines = existing_code.split('\n')
        for line in existing_lines:
            if line.startswith('package '):
                existing_package_line = line
                break

        # 保留新代码中的package声明
        new_package_line = ''
        new_lines = new_code.split('\n')
        for line in new_lines:
            if line.startswith('package '):
                new_package_line = line
                break

        # 如果现有代码中没有package声明，但新代码中有，则使用新代码中的package声明
        if not existing_package_line and new_package_line:
            existing_code = new_package_line + '\n\n' + existing_code

        # 移除新代码中的package声明行
        new_code_without_package = '\n'.join([line for line in new_lines if not line.startswith('package ')])

        # 提取现有代码中的import块
        existing_import_start = existing_code.find('import (')
        existing_import_end = -1
        if existing_import_start != -1:
            bracket_count = 1
            existing_import_end = existing_import_start + len('import (')
            while existing_import_end < len(existing_code) and bracket_count > 0:
                if existing_code[existing_import_end] == '(':
                    bracket_count += 1
                elif existing_code[existing_import_end] == ')':
                    bracket_count -= 1
                existing_import_end += 1
            existing_import_block = existing_code[existing_import_start:existing_import_end]
        else:
            existing_import_block = ''

        # 提取新代码中的import块
        new_import_start = new_code_without_package.find('import (')
        new_import_end = -1
        if new_import_start != -1:
            bracket_count = 1
            new_import_end = new_import_start + len('import (')
            while new_import_end < len(new_code_without_package) and bracket_count > 0:
                if new_code_without_package[new_import_end] == '(':
                    bracket_count += 1
                elif new_code_without_package[new_import_end] == ')':
                    bracket_count -= 1
                new_import_end += 1
            new_import_block = new_code_without_package[new_import_start:new_import_end]
        else:
            new_import_block = ''

        # 如果都没有import块，直接返回
        if not existing_import_block and not new_import_block:
            return existing_code + '\n\n' + new_code_without_package

        # 提取现有的import语句
        existing_imports = set()
        if existing_import_block:
            for line in existing_import_block.split('\n'):
                line = line.strip()
                if line and not line.startswith('//') and not line.startswith('import (') and line != ')':
                    existing_imports.add(line)

        # 提取新的import语句
        new_imports = set()
        if new_import_block:
            for line in new_import_block.split('\n'):
                line = line.strip()
                if line and not line.startswith('//') and not line.startswith('import (') and line != ')':
                    new_imports.add(line)

        # 合并import语句
        merged_imports = existing_imports.union(new_imports)

        # 构建新的import块
        merged_import_block = 'import (\n    ' + '\n    '.join(sorted(merged_imports)) + '\n)' if merged_imports else ''

        # 构建合并后的代码
        if existing_import_block and new_import_block:
            # 替换现有代码中的import块
            merged_code = existing_code[:existing_import_start] + merged_import_block + existing_code[existing_import_end:]
            # 添加去除import块和package声明后的新代码
            new_code_without_import_package = new_code_without_package[:new_import_start] + new_code_without_package[new_import_end:]
            merged_code += '\n\n' + new_code_without_import_package
        elif existing_import_block:
            # 替换现有代码中的import块
            merged_code = existing_code[:existing_import_start] + merged_import_block + existing_code[existing_import_end:]
            # 添加去除package声明后的新代码
            merged_code += '\n\n' + new_code_without_package
        elif new_import_block:
            # 添加新的import块和去除package声明后的代码
            merged_code = existing_code + '\n\n' + merged_import_block + new_code_without_package[new_import_end:]
        else:
            merged_code = existing_code + '\n\n' + new_code_without_package

        return merged_code

    def _save_test_file(self, test_file_path: str, test_template_code: str, function_name: str) -> None:
        """
        保存测试用例模板文件
        :param test_file_path: 测试文件路径
        :param test_template_code: 测试用例模板代码
        :param function_name: 函数名
        """
        # 检查文件是否存在
        if os.path.exists(test_file_path):
            # 文件存在，检查是否已有该函数的测试
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否已有该函数的测试
            test_func_name = f"Test{function_name}"
            has_test_func = f"func {test_func_name}(" in content
            
            if has_test_func:
                self.logger.warning(f"函数{function_name}的测试已存在于{test_file_path}")
                return
            
            # 检查文件夹下是否已有TestMain函数
            dir_path = os.path.dirname(test_file_path)
            has_test_main = self._has_test_main_in_folder(dir_path)
            
            test_main_code = ""
            if not has_test_main:
                test_main_code = self._generate_test_main()
            # 使用_merge_imports方法合并测试函数代码，确保import语句不重复
            content = self._merge_imports(content, test_template_code)
            
            # 如果需要添加TestMain函数
            if test_main_code:
                content = self._merge_imports(content, test_main_code)
        else:
            # 文件不存在，创建新文件
            # 为新文件添加package声明
            dir_path = os.path.dirname(test_file_path)
            package_name = os.path.basename(dir_path)
            
            # 检查文件夹下是否已有TestMain函数
            has_test_main = self._has_test_main_in_folder(dir_path)
            
            test_main_code = ""
            if not has_test_main:
                test_main_code = self._generate_test_main(package_name)
                content = self._merge_imports(test_main_code, test_template_code)
            else:
                content = test_template_code
        
        # 保存文件
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"已保存测试文件到{test_file_path}")

    def _has_test_main_in_folder(self, folder_path: str) -> bool:
        """
        检查文件夹下所有_test.go文件是否包含TestMain函数
        :param folder_path: 文件夹路径
        :return: 如果有任何_test.go文件包含TestMain函数，则返回True；否则返回False
        """
        if not os.path.exists(folder_path):
            return False

        # 遍历文件夹下所有_test.go文件
        for file_name in os.listdir(folder_path):
            if file_name.endswith('_test.go'):
                file_path = os.path.join(folder_path, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'func TestMain(' in content:
                            return True
                except Exception as e:
                    self.logger.error(f"读取文件{file_path}时出错: {str(e)}")
        return False

    def _generate_test_main(self, package_name: str = "") -> str:
        """
        生成TestMain函数
        :param package_name: 包名，如果不为空则添加package声明
        :return: TestMain函数代码
        """
        package_line = f"package {package_name}\n\n" if package_name else ""
        return constants.TEST_MAIN_TEMPLATE.format(package_line=package_line)