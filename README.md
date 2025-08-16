# AutoUnitTestPro

自动生成Go单元测试的大模型工具

## 功能介绍

AutoUnitTestPro 是一个使用大模型自动为Go项目生成单元测试的工具。它能够分析Go项目中的代码，识别函数，并使用大模型生成符合要求的单元测试。

主要特性：
- 自动分析Go项目结构和函数
- 使用大模型生成高质量单元测试
- 支持表格驱动测试
- 支持正例和反例测试
- 自动处理依赖项模拟

## 安装

1. 确保已安装 Python 3.13 或更高版本
2. 使用uv安装依赖

```bash
uv install
```

## 配置

1. 复制 `.env.example` 到 `.env`
2. 编辑 `.env` 文件，配置API密钥和项目路径

```env
# 大模型API密钥配置
# OpenAI API密钥
# OPENAI_API_KEY=your_openai_api_key

# Anthropic API密钥
# ANTHROPIC_API_KEY=your_anthropic_api_key

# 硅基流动API密钥
# SILICONFLOW_API_KEY=your_siliconflow_api_key
# 硅基流动模型 (默认: deepseek-ai/deepseek-chat)
# SILICONFLOW_MODEL=deepseek-ai/deepseek-chat
# 硅基流动API URL (默认: https://api.siliconflow.cn/v1/chat/completions)
# SILICONFLOW_URL=https://api.siliconflow.cn/v1/chat/completions

# 项目配置
# GO_PROJECT_PATH=/path/to/your/go/project
# SERVICES_DIR=services
# TEST_TEMPLATE_DIR=templates
```

## 使用方法

### 基本使用

```bash
python main.py --project-path /path/to/your/go/project
```

### 选择大模型

支持的模型类型: openai, anthropic, siliconflow

```bash
python main.py --project-path /path/to/your/go/project --model-type anthropic
```

使用硅基流动模型:

```bash
python main.py --project-path /path/to/your/go/project --model-type siliconflow
```

## 项目结构

```
.\n├── .env              # 环境变量配置
├── .gitignore        # Git忽略文件
├── .python-version   # Python版本
├── README.md         # 项目说明
├── config.py         # 配置模块
├── code_analyzer.py  # 代码分析器
├── llm.py            # 大模型客户端
├── main.py           # 主程序入口
├── pyproject.toml    # 项目依赖配置
└── test_generator.py # 测试生成器
```

## 注意事项

1. 确保已配置有效的大模型API密钥
2. 目前支持OpenAI、Anthropic和硅基流动(SiliconFlow)的模型
3. 生成的测试可能需要根据实际情况进行调整
4. 仅支持Go项目的单元测试生成

## 贡献

欢迎提交PR和issue，帮助改进这个工具。