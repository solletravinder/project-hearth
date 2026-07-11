import { EmptyState } from '@/components/common/EmptyState';

export function NoteList() {
  return (
    <div className="flex-1 overflow-y-auto">
      <EmptyState
        title="No notes yet"
        description="Create notes to capture your thoughts and research."
      />
    </div>
  );
}
