import { watch } from 'vue'
import { useUserStore } from '@/stores/user'

export type SessionRefreshOptions = {
  /** 登录后拉取数据 */
  refresh: () => void
  /** 退出后清空页面上的用户数据 */
  clear?: () => void
}

/** 登录/退出时同步当前页数据 */
export function useSessionRefresh(refreshOrOpts: (() => void) | SessionRefreshOptions) {
  const opts: SessionRefreshOptions =
    typeof refreshOrOpts === 'function' ? { refresh: refreshOrOpts } : refreshOrOpts
  const store = useUserStore()
  const clear = opts.clear ?? (() => {})

  function syncSession() {
    if (store.isLoggedIn()) opts.refresh()
    else clear()
  }

  watch(() => store.sessionTick, syncSession)

  watch(
    () => store.user?.id,
    (id, prev) => {
      if (id) opts.refresh()
      else if (prev != null) clear()
    }
  )
}
