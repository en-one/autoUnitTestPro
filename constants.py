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