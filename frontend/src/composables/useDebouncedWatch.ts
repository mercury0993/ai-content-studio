import { watch, onUnmounted } from 'vue'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useDebouncedWatch(
  sources: any,
  callback: any,
  delay = 300,
  options?: any,
) {
  let timer: ReturnType<typeof setTimeout> | null = null

  const unwatch = watch(
    sources,
    (...args: any[]) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        callback(...args)
      }, delay)
    },
    options,
  )

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
    unwatch()
  })

  return unwatch
}
