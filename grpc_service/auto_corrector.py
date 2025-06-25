from typing import Tuple, List
import ast
import black
from isort import code as isort_code
import logging

class AutoCorrector:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # 自动修正代码-基础工具：基础语法检查 和 格式化
    # retn (formatted_code, syntax_ok, errors)
    def auto_correct_code(self, raw_code: str) -> Tuple[str, bool, List[str]]: 
        # 1. 语法检查
        syntax_ok, errors = self.check_syntax(raw_code)
        if not syntax_ok:
            # 语法不通过，直接返回原始代码和错误
            return raw_code, False, errors
        
        # 2. 格式化
        formatted_code = self.format_code(raw_code)
        
        # 3. 返回
        ok2, errs2 = self.check_syntax(formatted_code)
        if not ok2: 
            return formatted_code, False, errs2
        
        # 4. 删除未使用的导入
        formatted_code = self.remove_unused_imports(formatted_code)
        
        # 5. 排序导入
        formatted_code = self.sort_imports(formatted_code)
        
        return formatted_code, True, []
    
    # syntax_helper 语法检查
    def check_syntax(self, raw_code: str) -> Tuple[bool, List[str]]:
        # 语法检查
        errors: List[str] = []
        try:
            ast.parse(raw_code)
            syntax_ok = True
            return (syntax_ok, errors)
        except Exception as e:
            return False, [f"{str(e)} (line {getattr(e, 'lineno', '?')})"]
            
    # format_helper 代码格式化
    def format_code(self, raw_code: str) -> str:
        try:
            # Black 的默认模式，自动换行、缩进等
            mode = black.Mode()
            self.logger.debug("格式化前代码: %s", raw_code)
            formatted_code = black.format_str(raw_code, mode=mode)
            self.logger.debug("格式化后代码: %s", formatted_code)
            return formatted_code
        
        except Exception as e:
            self.logger.warning(f"Black 格式化失败：{e}")
            return raw_code
    
    # sort_imports_helper 排序导入
    def sort_imports(self, raw_code: str) -> str:
        return isort_code(raw_code)
    

    