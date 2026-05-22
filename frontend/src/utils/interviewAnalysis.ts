/** 从面试记录的 ai_analysis 字段解析出可展示的 AI 分析 JSON */
export function parseInterviewAiAnalysis(raw: unknown): Record<string, unknown> | null {
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
  if (obj.overall || obj.highlights || obj.improvements || obj.tabs || obj.score != null) {
    return obj
  }
  return null
}

export function isInterviewAdopted(row: { ai_adopted?: unknown }): boolean {
  return Boolean(row.ai_adopted)
}
