import { useState } from 'react';

interface NoteEditorProps {
  initialTitle?: string;
  initialContent?: string;
  onSave: (title: string, content: string) => void;
  onCancel?: () => void;
}

export function NoteEditor({ initialTitle = '', initialContent = '', onSave, onCancel }: NoteEditorProps) {
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);

  const handleSave = () => {
    if (!title.trim() && !content.trim()) return;
    onSave(title, content);
  };

  return (
    <div className="flex flex-col h-full p-4">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Note title..."
        className="w-full text-lg font-semibold bg-transparent border-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 mb-3"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Start writing..."
        className="flex-1 w-full resize-none bg-transparent border-none outline-none text-sm text-gray-700 dark:text-gray-300 placeholder-gray-400 dark:placeholder-gray-500 leading-relaxed"
      />
      <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-200 dark:border-hearth-700">
        {onCancel && (
          <button
            className="px-3 py-1 text-sm text-gray-300 dark:text-gray-400"
            onClick={onCancel}
          >
            Cancel
          </button>
        )}
        <button
          className="px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
          onClick={handleSave}
          disabled={!title.trim() && !content.trim()}
        >
          Save
        </button>
      </div>
    </div>
  );
}