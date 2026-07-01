import { useRef, useState, useCallback } from 'react';
import { ProgressBar } from '@/components/common/ProgressBar';

interface UploadZoneProps {
  onUpload: (files: FileList | File[]) => void;
  isUploading?: boolean;
}

export function UploadZone({ onUpload, isUploading = false }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        onUpload(e.dataTransfer.files);
      }
    },
    [onUpload],
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        onUpload(e.target.files);
      }
      // Reset so the same file can be selected again
      e.target.value = '';
    },
    [onUpload],
  );

  return (
    <div className="p-3 border-t border-gray-200 dark:border-hearth-700">
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileChange}
        accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md,.wav,.mp3,.ogg"
      />
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
          ${
            isDragging
              ? 'border-hearth-400 bg-hearth-50 dark:bg-hearth-800'
              : 'border-gray-300 dark:border-hearth-600 hover:border-hearth-400 dark:hover:border-hearth-500'
          }
          ${isUploading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        {isUploading ? (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">Uploading...</p>
            <ProgressBar value={50} className="max-w-xs mx-auto" />
          </div>
        ) : (
          <p className="text-xs text-gray-400 dark:text-gray-500">
            {isDragging ? 'Drop files here' : 'Drop files or click to upload'}
          </p>
        )}
      </div>
    </div>
  );
}
