/** 从简历记录的 ai_analysis 字段解析出可展示的 AI 分析 JSON */
export function parseResumeAiAnalysis(raw: unknown): Record<string, unknown> | null {
  if (raw == null || raw === '') return null
  let parsed: unknown = raw
  if (typeof raw === 'string') {
    parsed = tryParseJsonString(raw)
    if (parsed == null) return null
  }
  if (!parsed || typeof parsed !== 'object') return null
  const obj = parsed as Record<string, unknown>

  const nested = obj.analysis
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    const inner = normalizeResumeAnalysisPayload(nested as Record<string, unknown>)
    if (inner) return inner
  }

  return normalizeResumeAnalysisPayload(obj)
}

function tryParseJsonString(text: string): unknown {
  const trimmed = text.trim()
  try {
    return JSON.parse(trimmed)
  } catch {
    const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i)
    if (fenced?.[1]) {
      try {
        return JSON.parse(fenced[1].trim())
      } catch {
        return null
      }
    }
    const start = trimmed.indexOf('{')
    const end = trimmed.lastIndexOf('}')
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(trimmed.slice(start, end + 1))
      } catch {
        return null
      }
    }
    return null
  }
}

function normalizeResumeAnalysisPayload(obj: Record<string, unknown>): Record<string, unknown> | null {
  if (
    obj.score != null ||
    obj.overall ||
    obj.suggest_sections ||
    obj.tabs ||
    (Array.isArray(obj.highlights) && obj.highlights.length > 0) ||
    (Array.isArray(obj.improvements) && obj.improvements.length > 0)
  ) {
    return obj
  }
  if (typeof obj.legacy === 'string') {
    const legacy = parseResumeAiAnalysis(obj.legacy)
    if (legacy) return legacy
    return { overall: obj.legacy }
  }
  return null
}

/** 轮询任务返回的 result 可能与 DB 中结构一致，统一规范化 */
export function normalizeResumeAnalysisResult(result: unknown): Record<string, unknown> | null {
  if (result == null) return null
  if (typeof result === 'string') return parseResumeAiAnalysis(result)
  if (typeof result === 'object') {
    return parseResumeAiAnalysis(result)
  }
  return null
}

export function hasResumeAiAnalysis(row: Record<string, unknown>): boolean {
  return parseResumeAiAnalysis(row.ai_analysis) != null
}
