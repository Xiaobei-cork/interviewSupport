/** 从简历记录的 ai_analysis 字段解析出可展示的 AI 分析 JSON */
export function parseResumeAiAnalysis(raw: unknown): Record<string, unknown> | null {
  if (raw == null || raw === '') return null
  let parsed: unknown = raw
  if (typeof raw === 'string') {
    try {
      parsed = JSON.parse(raw)
    } catch {
      return null
    }
  }
  if (!parsed || typeof parsed !== 'object') return null
  const obj = parsed as Record<string, unknown>
  if (obj.score != null || obj.overall || obj.suggest_sections || obj.tabs || obj.highlights) {
    return obj
  }
  return null
}

export function hasResumeAiAnalysis(row: Record<string, unknown>): boolean {
  return parseResumeAiAnalysis(row.ai_analysis) != null
}
