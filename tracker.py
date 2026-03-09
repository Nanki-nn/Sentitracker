"""
资产情绪追踪器 (Asset Sentiment Tracker)
----------------------------------------
流程：
  1. 从 Alpha Vantage 拉取 NVDA / BTC 最新新闻标题
  2. 将标题发给所选 AI 模型，判断整体情绪（Bullish / Bearish / Neutral）
  3. 以 Markdown 格式打印分析结果

配置（模型、标的、API 密钥等）均在 config.py 中修改。
"""

import os
import sys
import requests
from datetime import datetime

# 所有可调参数集中在 config.py，这里只做逻辑
from config import (
    ALPHA_VANTAGE_API_KEY,
    ANALYST_MODEL,
    MAX_HEADLINES,
    TICKERS,
    SUPPORTED_MODELS,
    PROVIDER_KEY_ENV,
    PROVIDER_BASE_URL,
)


# ---------------------------------------------------------------------------
# 工具函数：模型 / 密钥解析
# ---------------------------------------------------------------------------

def resolve_provider(model: str) -> str:
    """根据模型名返回提供商标识，不支持时退出程序。"""
    provider = SUPPORTED_MODELS.get(model)
    if not provider:
        supported = "\n  ".join(SUPPORTED_MODELS.keys())
        sys.exit(f"ERROR: 不支持的模型 '{model}'。\n支持的模型：\n  {supported}")
    return provider


def get_api_key(provider: str) -> str:
    """读取对应提供商的 API 密钥，未设置时退出程序。"""
    env_var = PROVIDER_KEY_ENV[provider]
    key = os.environ.get(env_var, "")
    if not key:
        sys.exit(
            f"ERROR: 未设置 {env_var} 环境变量。\n"
            f"请先执行: export {env_var}=your_api_key"
        )
    return key


# ---------------------------------------------------------------------------
# 第一步：从 Alpha Vantage 拉取新闻标题
# ---------------------------------------------------------------------------

def fetch_headlines(ticker_symbol: str, limit: int = MAX_HEADLINES) -> list[str]:
    """
    调用 Alpha Vantage NEWS_SENTIMENT 接口，返回指定标的的新闻标题列表。
    若请求失败或触发限频，返回空列表。
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",  # 使用新闻情绪功能
        "tickers":  ticker_symbol,
        "limit":    limit,
        "apikey":   ALPHA_VANTAGE_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()  # 非 2xx 状态码时抛出异常
    except requests.RequestException as e:
        print(f"  [ERROR] 网络请求失败 ({ticker_symbol}): {e}")
        return []

    data = response.json()

    # Alpha Vantage 触发限频时会返回 "Information" 字段
    if "Information" in data:
        print(f"  [WARN] Alpha Vantage 限频提示: {data['Information']}")
        return []

    # 正常响应包含 "feed" 字段
    if "feed" not in data:
        print(f"  [WARN] 响应格式异常 ({ticker_symbol}): {data}")
        return []

    # 提取每条新闻的标题，过滤空值
    headlines = [item.get("title", "").strip() for item in data["feed"] if item.get("title")]
    return headlines[:limit]


# ---------------------------------------------------------------------------
# 第二步：调用 AI 模型分析情绪倾向（多提供商路由）
# ---------------------------------------------------------------------------

def build_prompt(display_name: str, headlines: list[str]) -> str:
    """构造统一的情绪分析 prompt，各提供商复用同一份。"""
    numbered = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
    return (
        f"You are a financial analyst. Below are the {len(headlines)} most recent news headlines "
        f"for {display_name}.\n\n"
        f"{numbered}\n\n"
        "Based only on these headlines, answer with:\n"
        "VIBE: <Bullish|Bearish|Neutral>\n"
        "REASON: <one concise sentence explaining the overall sentiment>\n"
        "Do not add any other text."
    )


def call_anthropic(model: str, api_key: str, prompt: str) -> str:
    """调用 Anthropic Claude API，返回原始文本。"""
    import anthropic  # 按需导入，避免未安装时报错

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=128,  # 回答极短，128 token 足够
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def call_openai_compatible(model: str, api_key: str, prompt: str, base_url: str) -> str:
    """
    通用 OpenAI 兼容接口调用（OpenAI / DeepSeek / Qwen 均走此函数）。
    base_url 由调用方从 config.PROVIDER_BASE_URL 传入。
    """
    from openai import OpenAI  # 按需导入

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def call_google(model: str, api_key: str, prompt: str) -> str:
    """调用 Google Gemini API，返回原始文本。"""
    import google.generativeai as genai  # 按需导入

    genai.configure(api_key=api_key)
    gemini = genai.GenerativeModel(model)
    response = gemini.generate_content(prompt)
    return response.text.strip()


def get_vibe(display_name: str, headlines: list[str], model: str, provider: str, api_key: str) -> tuple[str, str]:
    """
    将新闻标题发给指定 AI 模型，返回 (情绪标签, 一句话原因)。
    情绪标签取值：Bullish（看涨）/ Bearish（看跌）/ Neutral（中性）
    """
    if not headlines:
        return "Neutral", "No headlines were available to analyse."

    prompt = build_prompt(display_name, headlines)

    # 根据提供商路由到对应的调用逻辑
    if provider == "anthropic":
        raw = call_anthropic(model, api_key, prompt)
    elif provider == "google":
        raw = call_google(model, api_key, prompt)
    else:
        # openai / deepseek / qwen 均走 OpenAI 兼容接口，base_url 来自 config
        raw = call_openai_compatible(model, api_key, prompt, PROVIDER_BASE_URL[provider])

    return _parse_vibe(raw)


def _parse_vibe(raw: str) -> tuple[str, str]:
    """
    从模型输出中解析 VIBE 和 REASON 字段。
    解析失败时返回 Neutral 和原始文本作为兜底。
    """
    vibe, reason = "Neutral", raw

    for line in raw.splitlines():
        if line.upper().startswith("VIBE:"):
            vibe = line.split(":", 1)[1].strip().capitalize()
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    # 防御性校验：确保情绪标签在合法范围内
    if vibe.lower() not in {"bullish", "bearish", "neutral"}:
        vibe = "Neutral"

    return vibe, reason


# ---------------------------------------------------------------------------
# 第三步：格式化为 Markdown 输出
# ---------------------------------------------------------------------------

# 情绪标签 -> 颜色 emoji 映射
VIBE_EMOJI = {
    "bullish": "🟢",
    "bearish": "🔴",
    "neutral": "🟡",
}


def vibe_badge(vibe: str) -> str:
    """生成带 emoji 的情绪徽章，例如：🟢 **Bullish**"""
    emoji = VIBE_EMOJI.get(vibe.lower(), "⚪")
    return f"{emoji} **{vibe}**"


def render_markdown(results: list[dict], model: str) -> str:
    """将所有资产的分析结果拼装成 Markdown 字符串。"""
    lines = [
        "# 📊 Asset Sentiment Tracker",
        "",
        f"*Powered by Alpha Vantage news · Analysed by `{model}`*",
        "",
        "---",
        "",
    ]

    for r in results:
        # 每个资产输出：名称、情绪、原因、标题数量
        lines += [
            f"## {r['display_name']}",
            "",
            f"**Vibe:** {vibe_badge(r['vibe'])}",
            "",
            f"**Reason:** {r['reason']}",
            "",
            f"**Headlines analysed:** {r['headline_count']}",
            "",
        ]

        # 原始标题放在可折叠的 <details> 块里，避免刷屏
        if r["headlines"]:
            lines.append("<details>")
            lines.append("<summary>Show headlines</summary>")
            lines.append("")
            for i, h in enumerate(r["headlines"], 1):
                lines.append(f"{i}. {h}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主函数入口
# ---------------------------------------------------------------------------

def main():
    # 解析模型与提供商
    provider = resolve_provider(ANALYST_MODEL)
    api_key  = get_api_key(provider)

    # 提醒用户 demo key 的限制
    if ALPHA_VANTAGE_API_KEY == "demo":
        print(
            "WARNING: 当前使用 Alpha Vantage demo 密钥，数据有限。\n"
            "请设置 ALPHA_VANTAGE_API_KEY 以获取完整实时数据。\n"
        )

    print(f"使用模型: {ANALYST_MODEL} ({provider})\n")

    results = []

    # 依次处理每个标的
    for display_name, av_symbol in TICKERS.items():
        print(f"正在拉取 {display_name}（{av_symbol}）的新闻标题...")
        headlines = fetch_headlines(av_symbol)
        print(f"  获取到 {len(headlines)} 条标题，正在请求 {ANALYST_MODEL} 分析情绪...")
        vibe, reason = get_vibe(display_name, headlines, ANALYST_MODEL, provider, api_key)

        # 汇总结果
        results.append({
            "display_name":   display_name,
            "vibe":           vibe,
            "reason":         reason,
            "headlines":      headlines,
            "headline_count": len(headlines),
        })

    # 生成 Markdown 报告
    report = render_markdown(results, ANALYST_MODEL)

    # 打印到终端
    print()
    print(report)

    # 同时写入 .md 文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"报告已保存至: {filename}")


if __name__ == "__main__":
    main()
