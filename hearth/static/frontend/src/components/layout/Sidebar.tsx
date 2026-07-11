import { useNavigate } from 'react-router-dom';
import { useDocuments } from '@/hooks/useDocuments';
import { useChat } from '@/hooks/useChat';
import { useNotes } from '@/hooks/useNotes';


export function Sidebar() {
  const navigate = useNavigate();
  const { documents } = useDocuments();
  const { conversations } = useChat();
  const { notes } = useNotes();

  const sections = [
    {
      title: 'Documents',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      count: documents?.length ?? 0,
      emptyText: 'No documents yet',
      onClick: () => navigate('/documents'),
    },
    {
      title: 'Notes',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      count: notes?.length ?? 0,
      emptyText: 'No notes yet',
      onClick: () => navigate('/notes'),
    },
    {
      title: 'Chats',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
      count: conversations?.length ?? 0,
      emptyText: 'No conversations yet',
      onClick: () => navigate('/'),
    },
  ];

  return (
    <aside className="w-64 shrink-0 border-r border-gray-200 dark:border-hearth-700 bg-gray-50 dark:bg-hearth-800 overflow-y-auto">
      {sections.map((section) => (
        <div
          key={section.title}
          className="px-3 py-3 cursor-pointer group"
          onClick={section.onClick}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-gray-400 dark:text-gray-500">{section.icon}</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{section.title}</span>
            {section.count > 0 && (
              <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">{section.count}</span>
            )}
          </div>
          {section.count === 0 && (
            <p className="text-xs text-gray-400 dark:text-gray-500 pl-6">{section.emptyText}</p>
          )}
        </div>
      ))}
    </aside>
  );
}