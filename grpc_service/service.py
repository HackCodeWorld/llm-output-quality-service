from backend.llm_quality_pb2 import GenerateResponse, CodeCorrectResponse, TestResult
from backend.llm_quality_pb2_grpc import LLMQualityServiceServicer
from grpc_service.auto_corrector import AutoCorrector
from grpc_service.test_runner import TestRunner

class LLMQualityService(LLMQualityServiceServicer):
    
    def __init__(self):
        self.corrector = AutoCorrector()
        self.tester = TestRunner()
        
    def AutoCorrect(self, request, context):
        """
        gRPC接口：代码自动修正（语法+格式化）
        参数:
            request: CodeCorrectRequest
            context: gRPC context
        返回:
            CodeCorrectResponse
        """
        formatted_code, syntax_ok, syntax_errors = self.corrector.auto_correct_code(
            request.raw_code, entry_point=request.entry_point, prompt=request.prompt
        )
        
        return CodeCorrectResponse(
            formatted_code = formatted_code,
            syntax_ok = syntax_ok,
            syntax_errors = syntax_errors
        )

    def Generate(self, request, context):
        """
        gRPC接口：代码生成与评测
        参数:
            request: GenerateRequest
            context: gRPC context
        返回:
            GenerateResponse
        """
        
        if not request.response:
            # 没有代码，直接返回错误
            return GenerateResponse(
                code="",
                syntax_ok=False,
                
                syntax_errors=["No code provided in response field."],
                test_results=[],
                exec_time_ms=0.0
            )
        

        # 1. 先在原始代码上执行测试，计算 pass@k
        test_results = []
        exec_time_ms = 0.0
        
        is_humaneval = False

        # 优先判断 结构化 test_cases
        if request.test_cases:  
            test_cases = [
                {"case_id": f"case_{i}", "input": tc.input, "expected": tc.expected}
                for i, tc in enumerate(request.test_cases)
            ]
            test_results, exec_time_ms = self.tester.run_structured_tests(request.response, test_cases)
       
        elif request.raw_test_code:
            if request.prompt and not request.test_cases:
                is_humaneval = True
                test_results, exec_time_ms = self.tester.run_humaneval_test(
                    request.prompt,
                    request.response,
                    request.raw_test_code,
                    request.entry_point,
                )
            else:
                test_results, exec_time_ms = self.tester.run_raw_tests(
                    request.response, request.raw_test_code, request.entry_point
                )
            
        # 2. 测试完成后再执行代码修正（格式化+语法）
        formatted_code, syntax_ok, syntax_errors = self.corrector.auto_correct_code(
            request.response,
            entry_point=request.entry_point,
            prompt=request.prompt,
            humaneval=is_humaneval,
        )
        
        # 3. 构造响应
        return GenerateResponse(
            code=formatted_code,
            syntax_ok=syntax_ok,
            syntax_errors=syntax_errors,
            test_results=test_results,
            exec_time_ms=exec_time_ms
        )