import { onMounted, onUnmounted } from 'vue'

export function useKeydown(handlers: Record<string, (e: KeyboardEvent) => void>) {
  function onKeydown(e: KeyboardEvent) {
    const key = [
      e.ctrlKey ? 'Ctrl' : '',
      e.shiftKey ? 'Shift' : '',
      e.key,
    ].filter(Boolean).join('+')

    const handler = handlers[key]
    if (handler) {
      e.preventDefault()
      handler(e)
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}
