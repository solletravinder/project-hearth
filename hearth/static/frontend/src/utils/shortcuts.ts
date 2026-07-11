export type ShortcutAction =
  | { action: 'search' }
  | { action: 'new-note' }
  | { action: 'send' }
  | { action: 'clear-chat' }
  | { action: 'open-settings' }
  | { action: 'close-panel' }
  | { action: 'upload' }
  | { action: 'toggle-pii' };

type ShortcutHandler = (action: ShortcutAction) => void;

interface ShortcutDef {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: ShortcutAction;
}

const SHORTCUTS: ShortcutDef[] = [
  { key: 'k', ctrl: true, action: { action: 'search' } },
  { key: 'n', ctrl: true, action: { action: 'new-note' } },
  { key: 'Enter', ctrl: true, action: { action: 'send' } },
  { key: 'c', ctrl: true, shift: true, action: { action: 'clear-chat' } },
  { key: ',', ctrl: true, action: { action: 'open-settings' } },
  { key: 'Escape', action: { action: 'close-panel' } },
  { key: 'u', ctrl: true, shift: true, action: { action: 'upload' } },
  { key: 'p', ctrl: true, shift: true, action: { action: 'toggle-pii' } },
];

export function handleKeyDown(e: KeyboardEvent, cb: ShortcutHandler): void {
  for (const sc of SHORTCUTS) {
    const match =
      sc.key === e.key &&
      (sc.ctrl ? e.ctrlKey || e.metaKey : true) &&
      (sc.shift ? e.shiftKey : !e.shiftKey);

    if (match) {
      e.preventDefault();
      cb(sc.action);
      return;
    }
  }
}

/**
 * Register keyboard shortcuts. Returns a cleanup function.
 */
export function registerShortcuts(cb: ShortcutHandler): () => void {
  const handler = (e: KeyboardEvent) => handleKeyDown(e, cb);
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
