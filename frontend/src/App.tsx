import { useState, useCallback } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { ChatView } from './components/chat/ChatView';
import { SettingsPanel } from './components/settings/SettingsPanel';
import { SearchDialog } from './components/search/SearchDialog';
import { useKeyboard } from './hooks/useKeyboard';
import type { ShortcutAction } from './utils/shortcuts';

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const handleShortcut = useCallback((action: ShortcutAction) => {
    switch (action.action) {
      case 'search':
        setSearchOpen((p) => !p);
        break;
      case 'open-settings':
        setSettingsOpen((p) => !p);
        break;
      case 'close-panel':
        setSettingsOpen(false);
        setSearchOpen(false);
        break;
      default:
        break;
    }
  }, []);

  useKeyboard(handleShortcut);

  return (
    <>
      <AppLayout
        onOpenSearch={() => setSearchOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      >
        <ChatView />
      </AppLayout>
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SearchDialog isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
