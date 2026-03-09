"""
config.py — 所有可调配置集中在此，按需修改后重新运行即可。

分三块：
  1. 运行时参数   — 模型选择、新闻条数、追踪标的
  2. 模型注册表   — 新增 / 删除模型只需改这里
  3. 提供商元数据 — API 密钥环境变量名、OpenAI 兼容接口的 base_url

API 密钥统一放在 .env 文件中，启动时自动加载。
"""

import os
from dotenv import load_dotenv

# 自动读取项目根目录的 .env 文件，将其中的键值注入环境变量
# override=False：不覆盖 shell 中已存在的同名变量
load_dotenv(override=False)

# ===========================================================================
# 1. 运行时参数
# ===========================================================================

# Alpha Vantage API 密钥（免费申请：alphavantage.co）
# 未设置时以 "demo" 模式运行，数据极为有限
ALPHA_VANTAGE_API_KEY: str = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# 使用的 AI 分析模型，通过环境变量指定，默认 Claude Opus
# 示例：export ANALYST_MODEL=gpt-4o
ANALYST_MODEL: str = os.environ.get("ANALYST_MODEL", "claude-opus-4-6")

# 每个标的最多传给模型的新闻条数（条数越多分析越准，token 消耗也越多）
MAX_HEADLINES: int = 10

# 待追踪的资产：{ 显示名称: Alpha Vantage 代码 }
# 股票直接用 ticker；加密货币需加 "CRYPTO:" 前缀
TICKERS: dict[str, str] = {
    "NVDA": "NVDA",
    "BTC":  "CRYPTO:BTC",
    # 可继续添加，例如：
    # "AAPL": "AAPL",
    # "ETH":  "CRYPTO:ETH",
}

# ===========================================================================
# 2. 模型注册表：模型名 -> 提供商标识
#    新增模型：在对应提供商区块追加一行即可
# ===========================================================================
SUPPORTED_MODELS: dict[str, str] = {
    # ---------- Anthropic Claude ----------
    "claude-opus-4-6":        "anthropic",
    "claude-sonnet-4-5":      "anthropic",
    "claude-haiku-4-5":       "anthropic",

    # ---------- OpenAI GPT ----------
    "gpt-4o":                 "openai",
    "gpt-4o-mini":            "openai",
    "gpt-4-turbo":            "openai",

    # ---------- Google Gemini ----------
    "gemini-2.0-flash":       "google",
    "gemini-1.5-pro":         "google",
    "gemini-1.5-flash":       "google",

    # ---------- DeepSeek ----------
    "deepseek-chat":          "deepseek",
    "deepseek-reasoner":      "deepseek",

    # ---------- Qwen 通义千问 ----------
    "qwen-max":               "qwen",
    "qwen-plus":              "qwen",
    "qwen-turbo":             "qwen",
}

# ===========================================================================
# 3. 提供商元数据
# ===========================================================================

# 每个提供商对应的 API 密钥环境变量名
PROVIDER_KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",   # console.anthropic.com
    "openai":    "OPENAI_API_KEY",      # platform.openai.com
    "google":    "GOOGLE_API_KEY",      # aistudio.google.com
    "deepseek":  "DEEPSEEK_API_KEY",    # platform.deepseek.com
    "qwen":      "DASHSCOPE_API_KEY",   # dashscope.aliyuncs.com
}

# OpenAI 兼容接口的自定义 base_url
# anthropic / google 使用官方 SDK，无需在此配置
PROVIDER_BASE_URL: dict[str, str] = {
    "openai":   "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1",
}
