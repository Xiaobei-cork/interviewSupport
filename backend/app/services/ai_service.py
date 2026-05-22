import json
from typing import Any

from app.config import get_settings

settings = get_settings()

STRICT_GROUNDING_RULES = """
【硬性规则 - 必须遵守】
1. 仅根据用户消息中明确提供的材料进行分析，禁止使用训练数据中的示例简历、模板候选人、历史对话或臆测内容。
2. 材料中未出现的公司、项目、技术栈、工具、产品、数据指标一律不得写入；岗位 JD 中列出的要求可以讨论。
3. 无录音转写时：在 overall 开头说明「未提供面试录音转写，无法评价现场问答细节；本次分析仅供参考」，然后必须结合岗位名称与岗位 JD 给出实质性分析与建议（岗位要求解读、能力匹配、备考重点、可能考点等）。备注很短或为空时，仍以 JD 与岗位为主进行分析，不得因备注少而拒绝输出或只写「材料不足无法分析」。
4. 不得编造任何面试对话、问答过程、简历经历或材料外的个人背景。
5. score（0-5）应反映基于现有材料对岗位匹配度与准备程度的评估；有 JD 时通常不应低于 2.5，除非 JD 与备注明确显示严重不匹配。
"""


def _require_deepseek() -> None:
    if not settings.deepseek_enabled:
        raise RuntimeError(
            "DeepSeek API 未配置：请在 .env 中设置 DEEPSEEK_API_KEY 后重启后端"
        )


def _minimal_interview_result(
    company_name: str,
    job_title: str,
    job_jd: str,
    remark: str,
    has_audio: bool,
) -> dict[str, Any]:
    """无 DeepSeek 时基于真实字段生成结果，优先依据岗位与 JD。"""
    jd = job_jd.strip()
    rm = remark.strip()
    disclaimer = (
        "未提供面试录音转写，无法评价现场问答细节；本次分析仅供参考。"
        if not has_audio
        else "已上传录音但未配置转写，无法评价对话细节；本次分析仅供参考。"
    )
    jd_hint = (
        f"结合岗位「{job_title}」与 JD 内容，建议梳理核心技能点与项目案例，针对 JD 关键词准备可量化成果。"
        if jd
        else f"岗位「{job_title}」未附详细 JD，建议补充 JD 后获得更精准的准备建议。"
    )
    overall = f"{disclaimer} 针对 {company_name} / {job_title}：{jd_hint}"
    if rm:
        overall += f" 备注要点：{rm[:200]}"
    highlights = []
    if jd:
        highlights.append("已提供岗位 JD，可据此拆解能力要求与备考方向")
    if rm:
        highlights.append("用户备注已记录，可结合 JD 做针对性复盘")
    improvements = [
        "对照 JD 逐条准备技能与项目案例的 STAR 表述",
        "梳理该岗位常见技术面与业务面问题清单",
    ]
    if has_audio:
        improvements.append("配置语音转写后可补充对答环节的细节复盘")
    elif not rm:
        improvements.append("可补充面试过程备注以便更精准复盘")
    return {
        "score": 3.2 if jd else 3.0,
        "highlights": highlights or [f"目标岗位：{job_title}"],
        "improvements": improvements,
        "overall": overall,
        "tabs": {
            "comprehensive": overall,
            "problems": jd_hint if jd else "建议补充岗位 JD 以识别能力差距与备考重点。",
            "highlights_eval": rm or (jd[:300] if jd else "可结合岗位名称准备通用能力展示。"),
            "plan": "1. 精读 JD 提炼关键词\n2. 准备 2-3 个匹配项目案例\n3. 模拟该岗位高频面试题",
        },
    }


async def analyze_interview(
    company_name: str,
    job_title: str,
    job_jd: str,
    remark: str,
    transcript: str,
    has_audio: bool,
) -> dict[str, Any]:
    if not settings.deepseek_enabled:
        return _minimal_interview_result(company_name, job_title, job_jd, remark, has_audio)

    user_payload = f"""【本次面试复盘材料 - 仅限以下内容，不得引用材料外信息】

公司名称：{company_name}
岗位名称：{job_title}

岗位 JD：
{job_jd.strip() or "（未填写）"}

用户备注：
{remark.strip() or "（未填写）"}

是否已上传面试录音文件：{"是" if has_audio else "否"}

面试录音文字转写（无转写则不得编造任何问答）：
{transcript.strip() if transcript.strip() else "（无转写文本）"}
"""
    system = (
        STRICT_GROUNDING_RULES
        + "\n你是专业面试教练。只分析上述材料。"
        "以JSON返回："
        '{"score":3.5,"highlights":[],"improvements":[],"overall":"",'
        '"tabs":{"comprehensive":"","problems":"","highlights_eval":"","plan":""}}'
        " highlights/improvements 各 2-4 条；tabs 各栏 80-300 字，须含基于 JD 的具体建议。"
        " overall 先写材料范围声明（有无录音转写），再写 JD/岗位导向的综合评价。"
    )
    return await _call_deepseek(system, user_payload)


async def analyze_resume(resume_text: str) -> dict[str, Any]:
    _require_deepseek()
    text = (resume_text or "").strip()
    if len(text) < 80:
        text = (
            "【系统说明】简历正文缺失或过短，无法做实质性分析。"
            "请仅说明材料不足，不要编造简历内容。\n"
            f"实际获取到的文本：{text or '（空）'}"
        )
    user_payload = f"""【本次简历分析材料 - 仅限以下正文，不得引用材料外信息】

{text[:8000]}
"""
    system = (
        STRICT_GROUNDING_RULES
        + "\n你是专业简历顾问。只分析上述简历正文。"
        "以JSON返回："
        '{"score":4.0,"highlights":[],"improvements":[],"overall":"",'
        '"tabs":{"comprehensive":"","problems":"","highlights_eval":"","plan":""},'
        '"suggest_sections":{"comprehensive":[{"icon":"star","title":"总体评价","content":""},'
        '{"icon":"warn","title":"核心问题","content":[]},'
        '{"icon":"target","title":"关键优化方向","content":[]},'
        '{"icon":"bulb","title":"优化建议","content":""}],'
        '"problems":[{"icon":"warn","title":"","content":""}],'
        '"highlights_eval":[{"icon":"star","title":"","content":""}],'
        '"plan":[{"icon":"target","title":"","content":""}]}}'
        " content 可为字符串或字符串数组；icon 仅 star/warn/target/bulb。"
        " 正文过短时 score 宜偏低，overall 说明材料不足。"
    )
    return await _call_deepseek(system, user_payload)


async def chat_interview(context: str, message: str) -> str:
    _require_deepseek()
    system = (
        STRICT_GROUNDING_RULES
        + "\n你是面试教练。仅根据【背景材料】回答，不得引入背景外的经历或简历信息。"
        f"\n\n【背景材料】\n{context[:4000]}"
    )
    return await _call_deepseek_text(system, message)


async def deep_optimize_resume(resume_text: str, requirement: str) -> dict[str, Any]:
    _require_deepseek()
    system = (
        STRICT_GROUNDING_RULES
        + "\n你是专业简历优化师。仅根据下方原始简历与用户要求输出优化稿，不得添加原文没有的经历。"
        "以JSON返回："
        '{"preview":{"name":"","phone":"","email":"","location":"","summary":"",'
        '"experiences":[{"period":"","company":"","title":"","current":false,"bullets":[]}]}}'
    )
    user = (
        f"用户优化要求：{requirement}\n\n"
        f"【原始简历 - 仅限以下内容】\n{resume_text[:8000]}"
    )
    return await _call_deepseek(system, user)


async def chat_resume(context: str, message: str) -> str:
    _require_deepseek()
    system = (
        STRICT_GROUNDING_RULES
        + "\n你是简历顾问。仅根据【背景材料】回答，不得编造简历中没有的内容。"
        f"\n\n【背景材料】\n{context[:4000]}"
    )
    return await _call_deepseek_text(system, message)


async def _call_deepseek(system: str, user: str) -> dict[str, Any]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    resp = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


async def _call_deepseek_text(system: str, user: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    resp = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content or ""
