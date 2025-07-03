import os
import subprocess
import tempfile
import time
from typing import List, Dict, Tuple
from backend.llm_quality_pb2 import TestResult
import logging

class TestRunner:
    """
    在 Docker 沙箱里执行测试用例，支持结构化 TestCase 和 raw_test_code。
    返回 List[TestResult]，每条记录包含 case_id, passed, errors.
    """
    
    logger = logging.getLogger(__name__)

    DOCKER_IMAGE = "python:3.10-slim"  # 轻量基础镜像
    TIMEOUT_SEC = int(os.getenv("TIMEOUT_SEC", "5"))  # 默认 5 秒

    @staticmethod
    def run_structured_tests(code: str, test_cases: List[Dict]) -> Tuple[List[TestResult], float]:
        """
        test_cases: List of {"case_id": str, "input": str, "expected": str}
        :returns:
          - List[TestResult]: 每条 case 的执行结果
          - float: 所有 case 的累计耗时（ms）
        """
        
        total_ms = 0.0
        results = []
        for tc in test_cases:
            # 为每个 case 单独运行，隔离资源
            payload = f"{code}\n\n" \
                      f"result = {tc['input']}\n" \
                      f"assert result == {tc['expected']}\n" \
                      f"print('PASS')"

            passed, errors, ms = TestRunner._run_in_docker(payload)
            
            total_ms += ms
            
            results.append(TestResult(
                case_id=tc["case_id"],
                passed=passed,
                errors=errors
            ))
        return results, total_ms

    @staticmethod
    def run_raw_tests(code: str, raw_test_code: str, entry_point: str) -> Tuple[List[TestResult], float]:
        """
        raw_test_code: 一整段例如多条 assert/pytest 风格代码
        视为一个测试套件，case_id 用 'raw'
        entry_point: 函数名儿
        :returns:
          - List[TestResult]: 单条 raw 用例的执行结果（case_id='raw'）
          - float: 该 raw 测试的耗时（ms）
        """
        payload = f"{code}\n\n{raw_test_code}\n\ncheck({entry_point})"
        passed, errors, ms = TestRunner._run_in_docker(payload)
        return [TestResult(case_id="raw", passed=passed, errors=errors)], ms    

    @staticmethod
    def _run_in_docker(python_code: str) -> Tuple[bool, List[str], float]:
        """
        在 Docker 容器内执行一段 Python 代码，返回 (passed, errors, elapsed_ms)
        """
        
        TestRunner.logger.info("开始在 Docker 中执行测试代码")

        # 1. 写入临时文件
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
            f.write(python_code)
            host_path = f.name

        # 2. 调用 Docker
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            f"--memory=256m", f"--cpus=0.5",
            # 宿主机临时文件挂载到容器内/code/test.py路径
            f"--volume={host_path}:/code/test.py:ro",
            TestRunner.DOCKER_IMAGE,
            "timeout", str(TestRunner.TIMEOUT_SEC),
            "python", "/code/test.py"
        ]
        
        start = time.time()
        
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            elapsed = (time.time() - start) * 1000
            TestRunner.logger.debug("Docker 执行输出: %s", output)
            # 如果输出中包含 PASS 则认为通过
            passed = "PASS" in output
            return passed, [], elapsed
        except subprocess.CalledProcessError as e:
            # 超时或断言失败都会抛 CPE
            elapsed = (time.time() - start) * 1000
            errors = e.output.splitlines()[-5:]  # 取最后几行错误详情
            TestRunner.logger.error("Docker 执行失败: %s", e.output)
            return False, errors, elapsed
        finally:
            # 3. 无论成功或异常，都清理宿主机临时文件
            try:
                os.remove(host_path)
                TestRunner.logger.debug("已清理临时文件: %s", host_path)
            except OSError:
                pass
