import { useState } from 'react';
import { useNotes } from '@/hooks/useNotes';
import { EmptyState } from '@/components/common/EmptyState';
import { NoteEditor } from './NoteEditor';
import { NoteEdit } from './NoteEdit';
import type { Note } from '@/types';
import { apiClient } from '@/api/client';

export function NotesList() {
  const { notes, isLoading, error } = useNotes();
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [showNewNote, setShowNewNote] = useState(false);

  const handleCreateNote = async (title: string, content: string) => {
    try {
      await apiClient.notes.create({ title, content });
      setShowNewNote(false);
    } catch (err) {
      console.error('Failed to create note:', err);
    }
  };

  const handleUpdateNote = async (note: Note) => {
    try {
      await apiClient.notes.update(note.id, { title: note.title, content: note.content });
      setEditingNote(null);
    } catch (err) {
      console.error('Failed to update note:', err);
    }
  };

  const handleEditNote = (note: Note) => {
    setEditingNote(note);
    setShowNewNote(false);
  };

  const handleDeleteNote = async (noteId: string) => {
    try {
      await apiClient.notes.delete(noteId);
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400 dark:text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-gray-400 dark:border-hearth-600 border-b-2 border-transparent dark:border-hearth-800"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded">
        {error}
        <button
          className="ml-2 underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-hearth-700">
        <h2 className="text-xl font-bold">Notes</h2>
        {!editingNote && !showNewNote && (
          <button
            className="px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
            onClick={() => setShowNewNote(true)}
          >
            New Note
          </button>
        )}
      </div>

      {showNewNote && (
        <NoteEditor
          onSave={handleCreateNote}
          onCancel={() => setShowNewNote(false)}
        />
      )}

      {editingNote && (
        <NoteEdit
          note={editingNote}
          onSave={handleUpdateNote}
          onCancel={() => setEditingNote(null)}
        />
      )}

      {!showNewNote && !editingNote && (
        <div className="flex-1 overflow-y-auto">
          {notes.length === 0 ? (
            <EmptyState
              title="No Notes Yet"
              description="Create your first note to capture ideas, research, or important information."
            />
          ) : (
            <div className="p-4 space-y-3">
              {notes.map(note => (
                <div
                  key={note.id}
                  className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="p-3">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">{note.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{note.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(note.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                          onClick={() => handleEditNote(note)}
                        >
                          Edit
                        </button>
                        <button
                          className="text-sm text-red-600 dark:text-red-400 hover:underline"
                          onClick={() => handleDeleteNote(note.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}