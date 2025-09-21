# 在文件顶部导入必要的模块
import os
import subprocess
import time
import re
from typing import Dict, Any, Optional
import logging
from code_analyzer import GoCodeAnalyzer
import core.constants
from llm_utils.llm import LLMClient
from core.config import settings
from llm_utils.prompts import LLM_SUPPPLY_FAILCASE_ARGS_PROMPT, LLM_MERGE_TEST_TEMPLATE, LLM_DEBUG_TEST_TEMPLATE  # 导入新模板

class TestTemplateGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = GoCodeAnalyzer()
        self.llm_client = LLMClient()
        self.logger.info("LLM客户端初始化完成")

    def generate_test_case(self, file_path: str, function_name: str, use_llm: bool = True, test_case_type: str = "both") -> Dict[str, Any]:
        """
        为单个函数生成单元测试用例模板
        :param file_path: 包含函数的文件路径
        :param function_name: 要生成测试用例模板的函数名
        :param use_llm: 是否使用LLM补充测试用例参数，默认为True
        :param test_case_type: 测试用例类型，可选值: "fail"、"success"、"both"（默认）
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
            # 1.生成基础测试模板
            test_template_code = self.generate_test_case_template(target_func)
             # 保存测试代码
            test_file_path = self._get_test_file_path(file_path)
            self._save_test_file(test_file_path, test_template_code, function_name)
            
            # 2. 调用LLM补充测试参数
            test_case_type = "fail"
            self.logger.info(f"启用LLM，开始补充测试参数: 函数名={function_name}, 测试类型={test_case_type}")
            test_template_code = self.enhance_test_with_params(file_path, function_name, test_template_code, test_case_type)
            # 保存测试代码
            test_file_path = self._get_test_file_path(file_path)
            self._save_test_file(test_file_path, test_template_code, function_name, mode="update")
            
            # 3. 验证测试代码并进行自动调试
            self.logger.info(f"开始验证测试代码: {test_file_path}")
            debug_result = self._validate_and_debug_test(test_file_path, function_name, test_template_code)
            if debug_result['status'] == 'success':
                self.logger.info(f"测试验证和调试成功: 函数名={function_name}")
                return {
                    'function_name': function_name,
                    'file_path': file_path,
                    'test_file_path': test_file_path,
                    'status': 'success',
                    'message': '测试模板生成成功，已通过验证',
                    'debug_info': debug_result
                }
            else:
                self.logger.warning(f"测试验证和调试失败: {debug_result.get('error', '未知错误')}")
                return {
                    'function_name': function_name,
                    'file_path': file_path,
                    'test_file_path': test_file_path,
                    'status': 'success_with_warning',
                    'message': '测试模板生成成功，但自动验证/调试失败',
                    'debug_info': debug_result
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
    def generate_test_case_template(self, func_info: Dict[str, Any]) -> str:
        """
        为单个函数生成基础测试用例模板
        :param func_info: 函数信息
        :return: 生成的基础测试用例模板代码
        """
        function_name = func_info['name']
        file_path = func_info['file_path']
        case_tags = func_info['api_tags']
        
        # 确定包名
        target_dir = os.path.dirname(file_path)
        package_name = os.path.basename(target_dir)
        
        # 生成基础测试模板
        test_template = core.constants.TEST_FUNCTION_TEMPLATE.format(
            package_name=package_name,
            function_name=function_name,
            case_tags=case_tags,
        )
        
        return test_template
        
    def enhance_test_with_params(self, file_path: str, function_name: str, test_template: str, test_case_type: str = "both") -> str:
        """
        调用LLM补充测试用例参数并将结果更新到测试模板中
        :param file_path: 包含函数的文件路径
        :param function_name: 函数名
        :param test_template: 基础测试模板
        :param test_case_type: 测试用例类型，可选值: "fail"、"success"、"both"（默认）
        :return: 补充参数并更新后的测试模板
        """
        try:
            # 获取函数的完整代码
            function_code = self.code_analyzer.get_function_code(file_path, function_name)
            self.logger.info(f"函数代码: {function_code}")
            # 调用LLM补充测试参数
            supplemented_test_template = self._supplement_test_params(function_code, function_name, test_template, test_case_type)
            return supplemented_test_template
        except Exception as e:
            self.logger.error(f"调用LLM补充测试参数失败，使用基础模板: {str(e)}")
            # 失败时返回基础模板
            return test_template

    def _supplement_test_params(self, function_code: str, function_name: str, test_template: str, test_case_type: str = "both") -> str:
        """
        调用LLM补充测试用例参数并将结果更新到原始模板中
        :param function_code: 函数代码
        :param function_name: 函数名
        :param test_template: 测试模板
        :param test_case_type: 测试用例类型，可选值: "fail"、"success"、"both"（默认）
        :return: 补充参数并更新后的测试模板
        """
        try:
            self.logger.info(f"开始调用LLM补充测试参数: 函数名={function_name}, 测试类型={test_case_type}")
            
            # 初始化测试用例
            fail_test = ""
            success_test = ""
            
            # 根据测试用例类型生成相应的测试用例
            if test_case_type in ["fail", "both"]:
                # 生成失败测试用例
                self.logger.info(f"生成失败测试用例: 函数名={function_name}")
                fail_test = self.llm_client.generate_test(function_code, function_name, model_type="siliconflow", test_type="fail")
                
                # 检查失败测试用例结果是否为空
                if not fail_test.strip():
                    self.logger.warning(f"LLM返回空失败测试用例")
            
            if test_case_type in ["success", "both"]:
                # 生成成功测试用例
                self.logger.info(f"生成成功测试用例: 函数名={function_name}")
                success_test = self.llm_client.generate_test(function_code, function_name, model_type="siliconflow", test_type="success")
                
                # 检查成功测试用例结果是否为空
                if not success_test.strip():
                    self.logger.warning(f"LLM返回空成功测试用例")
            
            # 合并两个测试用例
            combined_test = ""
            if fail_test.strip() and success_test.strip():
                combined_test = f"{fail_test}\n{success_test}"
            elif fail_test.strip():
                combined_test = fail_test
            elif success_test.strip():
                combined_test = success_test
            else:
                self.logger.warning(f"LLM返回空测试用例结果，使用基础模板")
                return test_template
            
            self.logger.info(f"LLM调用成功，生成的测试代码总长度: {len(combined_test)}")
            
            # 使用从prompts.py导入的模板，而不是内联定义
            merge_prompt = LLM_MERGE_TEST_TEMPLATE.format(
                test_template=test_template,
                supplemented_test=combined_test
            )
            
            # 调用LLM执行合并操作
            merged_test_template = self.llm_client.generate_test(merge_prompt, function_name, model_type="siliconflow")
            
            # 检查合并结果是否为空
            if not merged_test_template.strip():
                self.logger.warning(f"LLM合并模板失败，使用生成的测试代码")
                return combined_test
            
            # 清理生成的代码，移除非代码内容
            cleaned_test = self._clean_generated_code(merged_test_template)
            
            self.logger.info(f"LLM成功将测试参数合并到模板中，合并后代码长度: {len(cleaned_test)}")
            return cleaned_test
        except Exception as e:
            self.logger.error(f"调用LLM补充测试参数失败: {str(e)}")
            # 失败时返回原始模板
            return test_template

    def _clean_generated_code(self, code: str) -> str:
        """
        清理生成的代码，移除非代码内容
        :param code: 生成的代码
        :return: 清理后的代码
        """
        try:
            # 首先检查是否有代码块标记
            if '```go' in code:
                # 提取代码块内容
                start_idx = code.find('```go') + len('```go')
                end_idx = code.rfind('```')
                if start_idx < end_idx:
                    code = code[start_idx:end_idx].strip()
            
            # 移除注释性文字（如测试执行命令等）
            lines = code.split('\n')
            cleaned_lines = []
            skip_section = False
            
            for line in lines:
                # 跳过注释掉的测试执行命令部分
                if '测试执行命令:' in line or '# 测试执行命令:' in line:
                    skip_section = True
                    continue
                if skip_section and ('```bash' in line or '```' in line):
                    skip_section = False
                    continue
                if skip_section:
                    continue
                
                # 移除主要变更等说明文字
                if '主要变更:' in line or '测试执行命令:' in line or '请查看' in line:
                    continue
                
                # 保留代码行
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        except Exception as e:
            self.logger.warning(f"清理生成的代码时出错: {str(e)}")
            return code

    def _get_test_file_path(self, source_file_path: str) -> str:
        """
        获取测试文件路径
        :param source_file_path: 源文件路径
        :return: 测试文件路径
        """
        dir_name, file_name = os.path.split(source_file_path)
        base_name = os.path.splitext(file_name)[0]
        return os.path.join(dir_name, f"{base_name}_test.go")
    

    def _validate_and_debug_test(self, test_file_path: str, function_name: str, test_code: str) -> Dict[str, Any]:
        """
        验证测试代码并在失败时进行自动调试
        :param test_file_path: 测试文件路径
        :param function_name: 函数名
        :param test_code: 初始测试代码
        :return: 验证和调试结果
        """
        max_debug_attempts = 5  # 最大调试次数
        current_code = test_code
        
        # 获取测试文件所在目录
        test_dir = os.path.dirname(test_file_path)
        
        for attempt in range(max_debug_attempts):
            self.logger.info(f"第{attempt + 1}次测试验证尝试")
            
            # 执行测试命令
            test_result = self._run_go_test(test_dir, function_name)
            
            if test_result['success']:
                self.logger.info(f"测试通过: {function_name}")
                return {
                    'status': 'success',
                    'attempts': attempt + 1,
                    'last_output': test_result['output']
                }
            
            # 测试失败，调用大模型进行调试
            self.logger.warning(f"测试失败，开始调试: {function_name}")
            try:
                # 准备调试提示
                debug_prompt = self._prepare_debug_prompt(function_name, current_code, test_result['output'])
                
                # 调用LLM进行调试
                debugged_code = self.llm_client.generate_test(debug_prompt, function_name, model_type="siliconflow")
                
                if not debugged_code.strip():
                    self.logger.error("大模型返回空的调试结果")
                    break
                
                # 更新当前代码并保存
                current_code = debugged_code
                self._save_test_file(test_file_path, current_code, function_name, mode="update")
                
                self.logger.info(f"大模型调试成功，已更新测试代码: {function_name}")
            except Exception as e:
                self.logger.error(f"大模型调试失败: {str(e)}")
                break
        
        # 达到最大调试次数或调试过程中出错
        return {
            'status': 'failed',
            'attempts': max_debug_attempts,
            'last_output': test_result['output'],
            'error': '达到最大调试次数或调试过程中出错'
        }
        
    def _run_go_test(self, test_dir: str, function_name: str) -> Dict[str, Any]:
        """
        运行Go测试命令并获取结果
        :param test_dir: 测试文件所在目录
        :param function_name: 函数名
        :return: 测试结果
        """
        test_func_name = f"Test{function_name}"
        command = f"go test -timeout 30s -run {test_func_name} -v"
        
        self.logger.info(f"在目录 {test_dir} 执行测试命令: {command}")
        
        try:
            # 执行命令并捕获输出
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=test_dir, 
                capture_output=True, 
                text=True, 
                timeout=30  # 设置超时时间
            )
            
            # 组合标准输出和标准错误
            output = f"{result.stdout}\n{result.stderr}"
            
            # 判断测试是否成功
            success = result.returncode == 0 and "PASS" in output
            
            return {
                'success': success,
                'output': output,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            self.logger.error("测试执行超时")
            return {
                'success': False,
                'output': '测试执行超时',
                'returncode': -1
            }
        except Exception as e:
            self.logger.error(f"执行测试命令失败: {str(e)}")
            return {
                'success': False,
                'output': f"执行测试命令失败: {str(e)}",
                'returncode': -1
            }
            
    def _prepare_debug_prompt(self, function_name: str, current_code: str, test_output: str) -> str:
        """
        准备调试提示信息
        :param function_name: 函数名
        :param current_code: 当前的测试代码
        :param test_output: 测试输出结果
        :return: 调试提示
        """
        return LLM_DEBUG_TEST_TEMPLATE.format(
            function_name=function_name,
            current_code=current_code,
            test_output=test_output
        )

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

    def _save_test_file(self, test_file_path: str, test_template_code: str, function_name: str, mode: str = "add") -> None:
        """
        保存测试用例模板文件
        :param test_file_path: 测试文件路径
        :param test_template_code: 测试用例模板代码
        :param function_name: 函数名
        :param mode: 保存模式，可选值: "add"（默认，仅当测试不存在时添加）或 "update"（覆盖已存在的测试）
        """
        # 检查文件是否存在
        if os.path.exists(test_file_path):
            # 文件存在，检查是否已有该函数的测试
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否已有该函数的测试
            test_func_name = f"Test{function_name}"
            has_test_func = f"func {test_func_name}(" in content
            
            if has_test_func and mode == "add":
                self.logger.warning(f"函数{function_name}的测试已存在于{test_file_path}")
                return
            elif has_test_func and mode == "update":
                # 移除已存在的测试函数
                self.logger.info(f"更新函数{function_name}的测试用例")
                # 找到函数的开始和结束位置
                func_start_pos = content.find(f"func {test_func_name}(")
                if func_start_pos != -1:
                    # 查找函数的结束位置（需要找到匹配的花括号）
                    brace_count = 0
                    i = func_start_pos
                    while i < len(content):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                break
                        i += 1
                    # 移除旧的测试函数
                    content = content[:func_start_pos] + content[i+1:]
            
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
        return core.constants.TEST_MAIN_TEMPLATE.format(package_line=package_line)