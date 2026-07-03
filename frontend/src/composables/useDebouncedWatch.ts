import { watch, onUnmounted, type WatchSource, type WatchCallback, type WatchOptions } from 'vue'

export function useDebouncedWatch<T>(
  sources: WatchSource<T> | WatchSource<T>[],
  callback: WatchCallback<T>,
  delay = 300,
  options?: WatchOptions,
) {
  let timer: ReturnType<typeof setTimeout> | null = null

  const unwatch = watch(
    sources,
    (...args: Parameters<WatchCallback<T>>) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        ;(callback as any)(...args)
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
