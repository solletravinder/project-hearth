import { NotesList } from '@/components/notes/NotesList';

export function NotesView() {
  return (
    <div className="flex flex-col h-full">
      <NotesList />
    </div>
  );
}