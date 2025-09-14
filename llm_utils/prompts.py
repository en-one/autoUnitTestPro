# 大模型提示模板

LLM_SUPPPLY_ARGS_PROMPT = """
    我们现在已经完成了测试代码框架的生成，接下来需要补充测试用例的参数。
    请严格遵循以下要求：
    
    函数代码:
    {code}

    函数名: {function_name}

    测试代码补充规则:
   1. 列举下，当reply.Status 为fail时， reply.result的返回值都有哪些
   2. 如果没有失败的返回，则结束
   3. 如果有失败返回，挑选其中一个错误返回,作为args.wantReply.result，
   4. 根据其reply.result ，构建body入参
   5. 需要校验 tt.args.wantReply.Result 与 tt.args.reply.Resul
   6. 无需关注其他问题，只需补充当前失败的用例
   7. 返回补充后的测试代码
    
    重要提示：不得改变测试函数的结构、测试用例的定义方式或断言逻辑。
    只需在现有框架中补充具体的参数值和预期结果。
    """

# 在文件中添加以下内容

LLM_MERGE_TEST_TEMPLATE = """我需要将LLM生成的测试用例参数合并到原始测试模板中。请只替换原始模板中的测试用例部分，保留其他所有内容。

原始测试模板：
{test_template}

LLM生成的测试用例：
{supplemented_test}

请提供合并后的完整测试模板，不要添加任何额外的解释或说明。"""

LLM_DEBUG_TEST_TEMPLATE = """以下是函数 {function_name} 的单元测试代码，但在执行时失败了。请分析测试失败的原因，并修复测试代码。

测试代码：
{current_code}

测试失败输出：
{test_output}

请提供修复后的完整测试代码，不要添加任何额外的解释或说明。"""