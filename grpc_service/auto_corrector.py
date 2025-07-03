import ast
import textwrap
import re
import logging
from typing import Tuple, List
import black
from isort import code as isort_code

class AutoCorrector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def auto_correct_code(
        self, raw_code: str, entry_point: str = "", prompt: str = ""
    ) -> Tuple[str, bool, List[str]]:
        """
        代码修正主入口：
        - 优先信任 code 字段（raw_code），只要有顶级 def ...，整体信任
        - 自动补全 code 和 prompt 里的所有 import 行（去重，补缺失）
        - code 不合法时，尝试从 code/prompt 里提取签名
        - 兜底：entry_point 兜底（如有），否则直接报错
        """
        code = raw_code.strip()
        # 1. 提取所有 import 行（去重，补缺失）
        code_imports = self.extract_import_lines(code)
        prompt_imports = self.extract_import_lines(prompt)
        # 只补 prompt 里 code 没有的 import
        missing_imports = prompt_imports - code_imports
        all_imports = "\n".join(sorted(code_imports | missing_imports))

        # 2. 优先信任 code 字段：只要有顶级 def ...，整体信任
        if self.has_top_level_def(code):
            code = textwrap.dedent(code)
            if all_imports:
                code = all_imports + "\n" + code
            syntax_ok, errors = self.check_syntax(code)
            if not syntax_ok:
                return code, False, errors
            formatted_code = self.format_code(code)
            ok2, errs2 = self.check_syntax(formatted_code)
            if not ok2:
                return formatted_code, False, errs2
            formatted_code = self.sort_imports(formatted_code)
            return formatted_code, True, []

        # 3. fallback: 尝试从 code 里用正则提取签名
        signature = self.extract_signature_from_code(code)
        if signature:
            body = textwrap.dedent(code)
            body = textwrap.indent(body, "    ")
            code_block = (all_imports + "\n" if all_imports else "") + f"{signature}\n{body}"
            syntax_ok, errors = self.check_syntax(code_block)
            if not syntax_ok:
                return code_block, False, errors
            formatted_code = self.format_code(code_block)
            ok2, errs2 = self.check_syntax(formatted_code)
            if not ok2:
                return formatted_code, False, errs2
            formatted_code = self.sort_imports(formatted_code)
            return formatted_code, True, []

        # 4. fallback: 尝试从 prompt 里提取签名（只对 HumanEval 有用）
        if prompt:
            signature = self.extract_signature_from_prompt(prompt)
            if signature:
                body = textwrap.dedent(raw_code)
                body = textwrap.indent(body, "    ")
                code_block = (all_imports + "\n" if all_imports else "") + f"{signature}\n{body}"
                syntax_ok, errors = self.check_syntax(code_block)
                if not syntax_ok:
                    return code_block, False, errors
                formatted_code = self.format_code(code_block)
                ok2, errs2 = self.check_syntax(formatted_code)
                if not ok2:
                    return formatted_code, False, errs2
                formatted_code = self.sort_imports(formatted_code)
                return formatted_code, True, []

        # 5. fallback: 用 entry_point 兜底（如有）
        if entry_point:
            code_block = (all_imports + "\n" if all_imports else "") + f"def {entry_point}(*args, **kwargs):\n    pass"
            syntax_ok, errors = self.check_syntax(code_block)
            return code_block, False, ["无法提取函数签名，已兜底生成万能函数"]

        # 6. 彻底兜底
        return "", False, ["无法提取函数签名，代码不合法"]

    def has_top_level_def(self, code: str) -> bool:
        """
        判断 code 里是否有顶级 def ...，允许前面有 import/注释/空行
        """
        try:
            for node in ast.iter_child_nodes(ast.parse(code)):
                if isinstance(node, ast.FunctionDef):
                    return True
            return False
        except Exception:
            return False

    def extract_import_lines(self, src: str) -> set:
        """
        提取 src 里的所有 import 行，返回 set
        """
        import_lines = set()
        for line in src.splitlines():
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                import_lines.add(line)
        return import_lines

    def extract_signature_from_code(self, code: str) -> str:
        """
        用正则从 code 里提取 def ... 函数签名
        """
        match = re.search(r"^def\s+\w+\s*\([^\)]*\)\s*:", code, re.MULTILINE)
        if match:
            return match.group(0).strip()
        return ""

    def extract_signature_from_prompt(self, prompt: str) -> str:
        """
        用正则从 prompt 里提取 def ... 函数签名
        """
        match = re.search(r"^def\s+\w+\s*\([^\)]*\)\s*:", prompt, re.MULTILINE)
        if match:
            return match.group(0).strip()
        # fallback: 行遍历
        for line in prompt.splitlines():
            if line.strip().startswith("def "):
                return line.strip()
        return ""

    def check_syntax(self, raw_code: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        try:
            ast.parse(raw_code)
            return True, errors
        except Exception as e:
            return False, [f"{str(e)} (line {getattr(e, 'lineno', '?')})"]

    def format_code(self, raw_code: str) -> str:
        try:
            mode = black.Mode()
            self.logger.debug("格式化前代码: %s", raw_code)
            formatted_code = black.format_str(raw_code, mode=mode)
            self.logger.debug("格式化后代码: %s", formatted_code)
            return formatted_code
        except Exception as e:
            self.logger.warning(f"Black 格式化失败：{e}")
            return raw_code

    def sort_imports(self, raw_code: str) -> str:
        return isort_code(raw_code)