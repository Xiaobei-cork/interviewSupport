/** 头像选择结果（延迟上传：仅在编辑页点「保存」时提交） */
export type AvatarPickResult =
  | { kind: 'preset'; url: string }
  | { kind: 'file'; file: File; previewUrl: string }
