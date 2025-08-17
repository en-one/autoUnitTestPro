# TestMain函数模板常量
TEST_MAIN_TEMPLATE = """{package_line}import (
    "fmt"
    "testing"
    "git.shining3d.com/cloud/dental/unit"
)

func TestMain(m *testing.M) {{
    fmt.Println("TestBegin")
    unit.InitTestConfig()

    p := unit.InitGlobalMonkeyPatch()
    defer func() {{
        p.Reset()
    }}()

    m.Run()
    fmt.Println("TestEnd")
}}"""

# 测试函数模板常量
TEST_FUNCTION_TEMPLATE = """package {package_name}
import (
    "context"
    "testing"
    
    "github.com/stretchr/testify/assert"
    "git.shining3d.com/cloud/util/service"
    ucommon "git.shining3d.com/cloud/util/common"
    // 添加其他必要的导入
)

func Test{function_name}(t *testing.T) {{
    type args struct {{
        ctx       context.Context
        args      *service.Args
        reply     *service.Replies
        wantReply *service.Replies
    }}

    tests := []struct {{
        name    string
        args    args
        wantErr bool
    }}{{
        // 正例测试用例
        {{
            name: "success_case",
            args: args{{
                ctx: context.Background(),
                args: &service.Args{{
                    Queries: ucommon.GetHttpQueriesBytes(map[string]string{{}}),
                    Body:    ucommon.GetHttpBodyBytes(map[string]interface{{}}{{}}),
                }},
                reply: &service.Replies{{}},
                wantReply: &service.Replies{{
                    Status: "success",
                    Code:   200,
                    Result: nil, // 根据期望结果填充
                }},
            }},
            wantErr: false,
        }},
        // 反例测试用例 - 参数错误
        {{
            name: "fail_case_invalid_params",
            args: args{{
                ctx: context.Background(),
                args: &service.Args{{
                    Queries: ucommon.GetHttpQueriesBytes(map[string]string{{}}),
                    Body:    ucommon.GetHttpBodyBytes(map[string]interface{{}}{{}}),
                }},
                reply: &service.Replies{{}},
                wantReply: &service.Replies{{
                    Status: "fail",
                    Code:   400,
                    Result: map[string]interface{{}}{{"error": "无效参数"}},
                }},
            }},
            wantErr: true,
        }},
        // 反例测试用例 - 业务错误
        {{
            name: "fail_case_business_error",
            args: args{{
                ctx: context.Background(),
                args: &service.Args{{
                    Queries: ucommon.GetHttpQueriesBytes(map[string]string{{}}),
                    Body:    ucommon.GetHttpBodyBytes(map[string]interface{{}}{{}}),
                }},
                reply: &service.Replies{{}},
                wantReply: &service.Replies{{
                    Status: "fail",
                    Code:   500,
                    Result: map[string]interface{{}}{{"error": "业务处理失败"}},
                }},
            }},
            wantErr: true,
        }},
    }}

    for _, tt := range tests {{
        t.Run(tt.name, func(t *testing.T) {{
            err := {function_name}(tt.args.ctx, tt.args.args, tt.args.reply)
            if (err != nil) != tt.wantErr {{
                t.Errorf("{function_name}() error = %v, wantErr %v", err, tt.wantErr)
            }}
            assert.Equal(t, tt.args.wantReply.Status, tt.args.reply.Status)
            assert.Equal(t, tt.args.wantReply.Code, tt.args.reply.Code)
            // 注意：实际测试中可能需要根据返回结果的结构调整断言方式
            // assert.Equal(t, tt.args.wantReply.Result, tt.args.reply.Result)
        }})
    }}

}}"""


LLM_SUPPPLY_ARGS_PROMPT = """
    我们现在已经完成了模版的生成，下面我们要创建函数调用大模型去补充测试用例。
    首先我们需要学会如何补充异常用例的参数，因为异常用例会比较容易创建
    
    函数代码:
    {code}

    函数名: {function_name}

    测试代码要求:
    1. 我们要了解被测试函数的逻辑,以及函数的参数和返回值,以及函数的业务逻辑
    2. 根据 被测试函数是使用了args.Body 还是 args.Queries 去判断我们需要补充哪些参数到测试用例中
    3. 首先根据services层中判断是否缺失哪些参数会返回错误信息，或者哪些参数不对会返回错误信息，构造失败用例
    4. 可根据返回的结果修改对应的测试用例中的wantReply.Code
    
    当添加完测试用例后，你可以通过cd命令到测试用例的当前目录下执行
    go test -run 测试用例函数名 -v 查看执行情况
    """