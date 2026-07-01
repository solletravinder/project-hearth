import { useCallback, useRef, useState } from 'react';
import { useDocStore } from '@/store/docStore';

export function UploadZone() {
  const { uploadFiles, isUploading, uploadProgress } = useDocStore();
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      if (fileArray.length > 0) {
        uploadFiles(fileArray);
      }
    },
    [uploadFiles],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  };

  return (
    <div className="px-4 py-3">
      <div
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
          isDragOver
            ? 'border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-hearth-600 hover:border-gray-400 dark:hover:border-hearth-500'
        } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a,.ogg,.txt,.md"
          className="hidden"
          onChange={handleInputChange}
        />
        {isUploading ? (
          <div className="space-y-2">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Uploading...{' '}
              {uploadProgress
                ? `${Math.round((uploadProgress.loaded / uploadProgress.total) * 100)}%`
                : ''}
            </div>
            {uploadProgress && (
              <div className="w-full bg-gray-200 dark:bg-hearth-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${(uploadProgress.loaded / uploadProgress.total) * 100}%`,
                  }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <span className="font-medium text-blue-500 dark:text-blue-400">
              Click to upload
            </span>{' '}
            or drag and drop
            <br />
            PDF, images, audio, text
          </div>
        )}
      </div>
    </div>
  );
}
