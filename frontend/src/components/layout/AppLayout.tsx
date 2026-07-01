import { useState } from 'react';
import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';

interface AppLayoutProps {
  children: ReactNode;
  onOpenSearch?: () => void;
  onOpenSettings?: () => void;
}

export function AppLayout({
  children,
  onOpenSearch,
  onOpenSettings,
}: AppLayoutProps) {
  const [sidebarOpen] = useState(true);

  const handleSearch = () => onOpenSearch?.();
  const handleSettings = () => onOpenSettings?.();

  return (
    <div className="flex flex-col h-screen">
      <Header onSearch={handleSearch} onSettings={handleSettings} />
      <div className="flex flex-1 overflow-hidden">
        {sidebarOpen && <Sidebar />}
        <main className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-hearth-900">
          {children}
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
