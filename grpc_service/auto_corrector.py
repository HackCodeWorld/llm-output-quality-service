import ast
from typing import Tuple, List
import black

class AutoCorrector:
    # 自动修正代码-基础工具：基础语法检查 和 格式化
    # retn (formatted_code, syntax_ok, errors)
    def auto_correct_code(raw_code: str) -> Tuple[str, bool, List[str]]: 
        # 1. 语法检查
        syntax_ok, errors = check_syntax(raw_code)
        if not syntax_ok:
            # 语法不通过，直接返回原始代码和错误
            return raw_code, False, errors
        
        # 2. 格式化
        formatted_code = format_code(raw_code)
        
        # 3. 返回
        ok2, errs2 = check_syntax(formatted_code)
        if not ok2:
            return formatted_code, False, errs2
        
        return formatted_code, True, []
    
    # syntax_helper 语法检查
    def check_syntax(raw_code: str) -> Tuple[bool, List[str]]:
        # 语法检查
        errors: List[str] = []
        try:
            ast.parse(raw_code)
            syntax_ok = True
            return (syntax_ok, errors)
        except Exception as e:
            errors.append(f"{e.msg} (line {e.lineno}, col {e.offset})")
            syntax_ok = False
            return (syntax_ok, errors)
            
    # format_helper 代码格式化
    def format_code(raw_code: str) -> str:
        try:
            # Black 的默认模式，自动换行、缩进等
            mode = black.Mode()
            formatted = black.format_str(raw_code, mode=mode)
            return formatted_code
        
        except Exception:
            return raw_code
    
    