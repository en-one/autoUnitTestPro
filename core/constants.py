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
        }},
    }}

    for _, tt := range tests {{
        t.Run(tt.name, func(t *testing.T) {{
            err := {function_name}(tt.args.ctx, tt.args.args, tt.args.reply)
            if (err != nil) {{
                t.Errorf("{function_name}() error = %v", err)
            }}
            assert.Equal(t, tt.args.wantReply.Status, tt.args.reply.Status)
            assert.Equal(t, tt.args.wantReply.Code, tt.args.reply.Code)
            // 注意：实际测试中可能需要根据返回结果的结构调整断言方式
            assert.Equal(t, tt.args.wantReply.Result, tt.args.reply.Result)
        }})
    }}

}}"""

# 从llm_utils导入提示模板
from llm_utils.prompts import LLM_SUPPPLY_FAILCASE_ARGS_PROMPT, LLM_SUPPPLY_SUCCESS_ARGS_PROMPT