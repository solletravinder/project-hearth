import { useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ChatView } from './components/chat/ChatView';
import { DocumentsView } from './components/layout/DocumentsView';
import { NotesView } from './components/layout/NotesView';
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
        setSettingsOpen(true);
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
    <Router>
      <AppLayout onOpenSearch={() => setSearchOpen(true)} onOpenSettings={() => setSettingsOpen(true)}>
        <Routes>
          <Route path="/" element={<ChatView />} />
          <Route path="/chat" element={<ChatView />} />
          <Route path="/documents" element={<DocumentsView />} />
          <Route path="/notes" element={<NotesView />} />
          <Route path="*" element={<ChatView />} />
        </Routes>
      </AppLayout>
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SearchDialog isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </Router>
  );
}