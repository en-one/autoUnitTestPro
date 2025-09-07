import os
import re
import logging
from typing import List, Dict, Any

class GoCodeAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Go函数定义正则表达式
        self.func_pattern = re.compile(r'func\s+(\w+)\s*\((.*?)\)\s*(.*?)\{', re.DOTALL)
        # Go文档注释正则表达式
        self.doc_comment_pattern = re.compile(r'(/\*\*.*?\*/|/\*.*?\*/|//.*?)(?=\s*func)', re.DOTALL|re.MULTILINE)
        # 匹配@apitags标签的正则表达式
        self.api_tags_pattern = re.compile(r'@apitags\s+([\w,]+)', re.MULTILINE)

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        分析Go文件，提取函数信息
        :param file_path: Go文件路径
        :return: 函数信息列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return self.analyze_code(content, file_path)
        except Exception as e:
            self.logger.error(f"分析文件{file_path}失败: {str(e)}")
            return []

    def analyze_code(self, code: str, file_path: str = "unknown.go") -> List[Dict[str, Any]]:
        """
        分析Go代码字符串，提取函数信息
        :param code: Go代码字符串
        :param file_path: 文件名
        :return: 函数信息列表
        """
        functions = []
        # 使用正则表达式提取函数
        matches = self.func_pattern.finditer(code)
        
        # 首先找到所有的文档注释
        doc_comments = {}  # 存储位置到注释的映射
        for doc_match in self.doc_comment_pattern.finditer(code):
            doc_comments[doc_match.end()] = doc_match.group(1).strip()

        for match in matches:
            func_name = match.group(1)
            params = match.group(2).strip()
            return_type = match.group(3).strip()
            
            # 提取函数体
            start_pos = match.end()
            end_pos = self._find_matching_brace(code, start_pos)
            if end_pos == -1:
                self.logger.warning(f"文件{file_path}中函数{func_name}缺少匹配的花括号")
                continue
            
            func_body = code[start_pos:end_pos].strip()
            
            # 提取完整函数代码
            full_func_code = code[match.start():end_pos+1]
            
            # 查找函数对应的文档注释
            doc_comment = ""
            # 寻找距离函数定义最近的文档注释
            closest_pos = -1
            for pos in doc_comments.keys():
                if pos < match.start() and pos > closest_pos:
                    closest_pos = pos
            if closest_pos != -1:
                doc_comment = doc_comments[closest_pos]
            
            # 提取@apitags标签
            api_tags = self._extract_api_tags(doc_comment)
            
            functions.append({
                'name': func_name,
                'params': params,
                'return_type': return_type,
                'body': func_body,
                'full_code': full_func_code,
                'file_path': file_path,
                'doc_comment': doc_comment,
                'api_tags': api_tags
            })
        
        return functions

    def _extract_api_tags(self, doc_comment: str) -> str:
        """
        从文档注释中提取@apitags标签的数据
        :param doc_comment: 文档注释
        :return: 标签字符串
        """
        match = self.api_tags_pattern.search(doc_comment)
        if match:
            return match.group(1)
        return ''

    def _find_matching_brace(self, code: str, start_pos: int) -> int:
        """
        查找匹配的花括号
        :param code: 代码字符串
        :param start_pos: 开始位置
        :return: 匹配的花括号位置，未找到返回-1
        """
        brace_count = 1
        for i in range(start_pos, len(code)):
            if code[i] == '{':
                brace_count += 1
            elif code[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
        return -1

    def find_go_files(self, directory: str) -> List[str]:
        """
        查找目录下所有Go文件
        :param directory: 目录路径
        :return: Go文件列表
        """
        go_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.go') and not file.endswith('_test.go'):
                    go_files.append(os.path.join(root, file))
        return go_files

    def get_function_code(self, file_path: str, function_name: str) -> str:
        """
        获取指定文件中指定函数的完整代码
        :param file_path: 文件路径
        :param function_name: 函数名
        :return: 函数完整代码
        """
        try:
            functions = self.analyze_file(file_path)
            for func in functions:
                if func['name'] == function_name:
                    return func['full_code']
            self.logger.warning(f"在文件{file_path}中未找到函数{function_name}")
            return ''
        except Exception as e:
            self.logger.error(f"获取函数{function_name}代码失败: {str(e)}")
            return ''

    def analyze_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        分析目录下所有Go文件
        :param directory: 目录路径
        :return: 函数信息列表
        """
        all_functions = []
        go_files = self.find_go_files(directory)
        
        for file in go_files:
            functions = self.analyze_file(file)
            all_functions.extend(functions)
        
        return all_functions