# 📊 Asset Sentiment Tracker

基于 **Alpha Vantage** 新闻数据 + **多种 AI 模型**分析的资产情绪追踪工具。
自动抓取 NVDA、BTC 最新资讯，由你选择的 AI 模型给出看涨 / 看跌 / 中性判断，并输出 Markdown 报告。

---

## 支持的 AI 模型

| 提供商 | 模型名（`ANALYST_MODEL`） | 所需密钥环境变量 |
|--------|--------------------------|----------------|
| **Anthropic** | `claude-opus-4-6` *(默认)* | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| **OpenAI** | `gpt-4o` | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4-turbo` | `OPENAI_API_KEY` |
| **Google** | `gemini-2.0-flash` | `GOOGLE_API_KEY` |
| **Google** | `gemini-1.5-pro` | `GOOGLE_API_KEY` |
| **Google** | `gemini-1.5-flash` | `GOOGLE_API_KEY` |
| **DeepSeek** | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| **DeepSeek** | `deepseek-reasoner` | `DEEPSEEK_API_KEY` |
| **Qwen 通义千问** | `qwen-max` | `DASHSCOPE_API_KEY` |
| **Qwen 通义千问** | `qwen-plus` | `DASHSCOPE_API_KEY` |
| **Qwen 通义千问** | `qwen-turbo` | `DASHSCOPE_API_KEY` |

> DeepSeek 和 Qwen 均兼容 OpenAI 接口，无需额外安装 SDK，复用 `openai` 包即可。

---

## 快速开始

### 1. 安装依赖

```bash
pip3 install requests anthropic openai google-generativeai
```

### 2. 配置 API 密钥

复制模板并填入你的真实 key：

```bash
cp .env.example .env
```

打开 `.env` 编辑：

```ini
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key   # 必填

# 选择一个 AI 提供商填写对应密钥
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=AIza...
# DEEPSEEK_API_KEY=sk-...
# DASHSCOPE_API_KEY=sk-...

ANALYST_MODEL=claude-opus-4-6   # 切换模型改这里
```

> `.env` 已被 `.gitignore` 屏蔽，密钥不会意外提交到 Git。

### 3. 选择模型并运行

```bash
# 默认使用 claude-opus-4-6
python3 tracker.py

# 切换到 GPT-4o
ANALYST_MODEL=gpt-4o python3 tracker.py

# 切换到 Gemini 2.0 Flash
ANALYST_MODEL=gemini-2.0-flash python3 tracker.py

# 切换到 DeepSeek
ANALYST_MODEL=deepseek-chat python3 tracker.py

# 切换到通义千问
ANALYST_MODEL=qwen-max python3 tracker.py
```

---

## 输出示例

```
使用模型: gpt-4o (openai)

正在拉取 NVDA（NVDA）的新闻标题...
  获取到 10 条标题，正在请求 gpt-4o 分析情绪...
正在拉取 BTC（CRYPTO:BTC）的新闻标题...
  获取到 10 条标题，正在请求 gpt-4o 分析情绪...

# 📊 Asset Sentiment Tracker

*Powered by Alpha Vantage news · Analysed by `gpt-4o`*

---

## NVDA

**Vibe:** 🟢 **Bullish**

**Reason:** Headlines highlight strong AI chip demand and record earnings beats.

**Headlines analysed:** 10

---

## BTC

**Vibe:** 🟡 **Neutral**

**Reason:** Mixed signals between ETF inflows and macroeconomic uncertainty.

**Headlines analysed:** 10

---
```

---

## 项目结构

```
.
├── .env           # 🔑 API 密钥（已被 .gitignore 屏蔽，不会提交）
├── .env.example   # 📋 密钥模板（提交到版本库供团队参考）
├── .gitignore
├── config.py      # ✏️  模型、标的等配置在此修改
├── tracker.py     # 业务逻辑（无需修改）
└── README.md
```

---

## 工作流程

```
Alpha Vantage API
      │  NEWS_SENTIMENT
      ▼
 fetch_headlines()
      │  标题列表
      ▼
  build_prompt()
      │  统一 prompt
      ▼
 ┌────┴─────────────────────────────┐
 │  ANALYST_MODEL 路由              │
 │                                  │
 │  anthropic  →  call_anthropic()  │
 │  openai     →  call_openai()     │
 │  google     →  call_google()     │
 │  deepseek   →  call_deepseek()   │
 │  qwen       →  call_qwen()       │
 └────┬─────────────────────────────┘
      │  原始文本
      ▼
parse_vibe_response()
      │  VIBE + REASON
      ▼
 render_markdown()
      │
      ▼
   终端输出 Markdown 报告
```

---

## 自定义配置

所有可调参数集中在 **`config.py`**，按需修改后重新运行即可，无需动 `tracker.py`。

```python
# config.py

MAX_HEADLINES = 10   # 每个标的传给模型的最大新闻条数

TICKERS = {
    "NVDA": "NVDA",          # 股票直接用 ticker
    "BTC":  "CRYPTO:BTC",    # 加密货币加 "CRYPTO:" 前缀
    # "AAPL": "AAPL",
    # "ETH":  "CRYPTO:ETH",
}

# 新增模型：在 SUPPORTED_MODELS 对应区块追加一行
SUPPORTED_MODELS = {
    ...
    "my-new-model": "openai",   # 如果是 OpenAI 兼容接口
}

# 新增提供商的 base_url（OpenAI 兼容接口才需要）
PROVIDER_BASE_URL = {
    ...
    "my-provider": "https://api.my-provider.com/v1",
}
```

---

## 注意事项

- Alpha Vantage 免费套餐限制 **25 次请求/天**，追踪 2 个标的每次运行消耗 2 次
- 若未设置 `ALPHA_VANTAGE_API_KEY`，脚本以 `demo` 模式运行，数据极为有限
- 各模型 SDK 按需导入，只需安装你实际要用的那个即可

---

## 依赖

| 包 | 用途 | 必需 |
|----|------|------|
| `requests` | 调用 Alpha Vantage REST API | 始终需要 |
| `anthropic` | 调用 Claude API | 使用 Claude 时 |
| `openai` | 调用 GPT / DeepSeek / Qwen API | 使用三者之一时 |
| `google-generativeai` | 调用 Gemini API | 使用 Gemini 时 |
