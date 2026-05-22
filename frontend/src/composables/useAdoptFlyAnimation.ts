import { ref, nextTick, type Ref } from 'vue'

export interface FlyPoint {
  x: number
  y: number
}

/**
 * 采纳动效：大星从按钮位置缩小飞至目标印章
 */
export function useAdoptFlyAnimation() {
  const flying = ref(false)
  const flyStyle = ref<Record<string, string>>({})

  async function playFly(
    fromEl: HTMLElement | null | undefined,
    toEl: HTMLElement | null | undefined,
    onComplete?: () => void
  ) {
    if (!fromEl || !toEl) {
      onComplete?.()
      return
    }
    const from = fromEl.getBoundingClientRect()
    const to = toEl.getBoundingClientRect()
    const size = 56
    const startX = from.left + from.width / 2 - size / 2
    const startY = from.top + from.height / 2 - size / 2
    const endX = to.left + to.width / 2 - size / 2
    const endY = to.top + to.height / 2 - size / 2

    flying.value = true
    flyStyle.value = {
      left: `${startX}px`,
      top: `${startY}px`,
      width: `${size}px`,
      height: `${size}px`,
      transform: 'scale(1)',
      opacity: '1',
    }
    await nextTick()
    requestAnimationFrame(() => {
      flyStyle.value = {
        left: `${endX}px`,
        top: `${endY}px`,
        width: `${28}px`,
        height: `${28}px`,
        transform: 'scale(0.45)',
        opacity: '0.95',
        transition: 'left 0.55s cubic-bezier(0.22, 1, 0.36, 1), top 0.55s cubic-bezier(0.22, 1, 0.36, 1), width 0.55s ease, height 0.55s ease, transform 0.55s ease',
      }
    })
    window.setTimeout(() => {
      flying.value = false
      onComplete?.()
    }, 580)
  }

  return { flying, flyStyle, playFly }
}

export function resolveEl(refVal: Ref<unknown>): HTMLElement | null {
  const v = refVal.value
  if (!v) return null
  if (v instanceof HTMLElement) return v
  const el = (v as { $el?: HTMLElement }).$el
  return el instanceof HTMLElement ? el : null
}
