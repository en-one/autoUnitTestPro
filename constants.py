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
    "git.shining3d.com/cloud/mythology/pkg/service"
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
         /* 
            @unitFunc Test{function_name}
            @unitCaseName success_case
            @unitCaseType normal
            @unitCaseTargetType api
            @unitCaseTarget {function_name}
            @unitCaseTags {case_tags}
            @unitCaseDesc 正例测试用例 - 成功
        */
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
        /* 
            @unitFunc Test{function_name}
            @unitCaseName fail_case_business_error
            @unitCaseType abnormal
            @unitCaseTargetType api
            @unitCaseTarget {function_name}
            @unitCaseTags {case_tags}
            @unitCaseDesc 反例测试用例 - 业务错误
        */
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
    我们现在已经完成了测试代码框架的生成，接下来需要补充测试用例的参数。
    请严格遵循以下要求：
    
    函数代码:
    {code}

    函数名: {function_name}

    测试代码补充规则:
    1. 阅读测试用例的代码
    2. 阅读对应业务逻辑代码，通过 "t.Run(tt.name, func(t *testing.T)" 下面一行的函数阅读代码，以及可能
    调用的control层函数以及models层函数
    3. 分析被测试函数的services层逻辑，确定它使用的是args.Body还是args.Queries来获取参数。
    4. 对于正例测试用例，补充必要且有效的参数值到对应的位置。
    5. 对于反例测试用例，根据services层代码中对参数的校验逻辑，构造以下类型的错误用例：
       a. 缺失必需参数
       b. 参数值为空或格式不正确
       c. 特殊分支条件不满足
    5. 补充完参数后，将对应参数仅修改补充到args.args.Body或args.args.Queries中
    6. 仅修改wantReply.Code和wantReply.Result以匹配预期的错误响应，不改变其他结构。
    7. 测试用例的数量应覆盖主要功能路径和异常场景，但不应冗余。
    
    重要提示：不得改变测试函数的结构、测试用例的定义方式或断言逻辑。
    只需在现有框架中补充具体的参数值和预期结果。
    
    测试执行命令:
    cd 到测试文件所在目录
    go test -run Test{function_name} -v
    """