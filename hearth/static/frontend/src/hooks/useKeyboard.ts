import { useEffect } from 'react';
import type { ShortcutAction } from '@/utils/shortcuts';
import { registerShortcuts } from '@/utils/shortcuts';

export function useKeyboard(handler: (action: ShortcutAction) => void): void {
  useEffect(() => {
    const cleanup = registerShortcuts(handler);
    return cleanup;
  }, [handler]);
}
