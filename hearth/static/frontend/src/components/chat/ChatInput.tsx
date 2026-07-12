import { useRef, useCallback, useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

type StatusType = 'uploading' | 'uploaded' | 'recording' | 'transcribing' | 'error';

interface StatusMsg {
  type: StatusType;
  text: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask anything... (Enter to send)',
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState<StatusMsg | null>(null);
  const statusTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showStatus = useCallback((type: StatusType, text: string, durationMs = 3000) => {
    setStatus({ type, text });
    if (statusTimeoutRef.current) clearTimeout(statusTimeoutRef.current);
    statusTimeoutRef.current = setTimeout(() => setStatus(null), durationMs);
  }, []);

  const clearStatus = useCallback(() => {
    setStatus(null);
    if (statusTimeoutRef.current) clearTimeout(statusTimeoutRef.current);
  }, []);

  const handleSubmit = useCallback(() => {
    const el = textareaRef.current;
    if (!el || disabled || !el.value.trim()) return;
    clearStatus();
    onSend(el.value.trim());
    el.value = '';
    el.style.height = 'auto';
  }, [onSend, disabled, clearStatus]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const handleInput = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  // ── File upload ────────────────────────────────────────────────

  const handleAttachClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      showStatus('uploading', `Uploading ${file.name}...`, 0);
      try {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch('/api/documents/upload', { method: 'POST', body: form });
        if (!res.ok) throw new Error(`Upload failed (${res.status})`);
        showStatus('uploaded', `Uploaded ${file.name}`, 3000);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        showStatus('error', msg, 4000);
      } finally {
        // Reset so the same file can be re-selected
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    },
    [showStatus],
  );

  // ── Microphone / voice input ───────────────────────────────────

  const startRecording = useCallback(async () => {
    clearStatus();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4' });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        // Stop all tracks from the stream
        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        if (blob.size === 0) {
          showStatus('error', 'No audio captured', 3000);
          return;
        }

        showStatus('transcribing', 'Transcribing...', 0);
        try {
          const form = new FormData();
          const ext = recorder.mimeType.includes('webm') ? 'webm' : 'mp4';
          form.append('file', blob, `recording.${ext}`);
          const res = await fetch('/api/chat/transcribe', { method: 'POST', body: form });
          if (!res.ok) throw new Error(`Transcription failed (${res.status})`);
          const data = await res.json();

          if (textareaRef.current) {
            const existing = textareaRef.current.value;
            const prefix = existing ? existing + ' ' : '';
            textareaRef.current.value = prefix + data.text;
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
            textareaRef.current.focus();
          }
          showStatus('uploaded', 'Voice transcribed', 2000);
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Transcription failed';
          showStatus('error', msg, 4000);
        }
      };

      recorder.onerror = () => {
        stream.getTracks().forEach((t) => t.stop());
        showStatus('error', 'Recording failed', 3000);
        setIsRecording(false);
      };

      recorder.start();
      setIsRecording(true);
      showStatus('recording', 'Recording... tap mic again to stop', 0);
    } catch {
      showStatus('error', 'Microphone access denied', 4000);
    }
  }, [showStatus, clearStatus]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  const handleMicClick = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // ── Status colors ──────────────────────────────────────────────

  const STATUS_COLORS: Record<StatusType, string> = {
    uploading: 'text-blue-600',
    uploaded: 'text-green-600',
    recording: 'text-red-600',
    transcribing: 'text-blue-600',
    error: 'text-red-600',
  };

  return (
    <div className="border-t border-gray-200 dark:border-hearth-700 bg-white dark:bg-hearth-900">
      {/* Status bar */}
      {status && (
        <div className="px-4 pt-2">
          <span className={`text-xs ${status.type ? STATUS_COLORS[status.type] ?? 'text-gray-500' : 'text-gray-500'}`}>
            {status.text}
          </span>
        </div>
      )}

      <div className="flex items-end gap-2 p-4 max-w-4xl mx-auto">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf,.docx,.md,.csv,.json,.png,.jpg,.jpeg,.gif,.webp,.mp3,.wav,.m4a,.ogg,.flac"
          onChange={handleFileChange}
          className="hidden"
          tabIndex={-1}
        />

        {/* Attach button */}
        <button
          onClick={handleAttachClick}
          disabled={disabled}
          className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-hearth-700 disabled:opacity-30 transition-colors"
          title="Attach file"
          aria-label="Attach file"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          disabled={disabled || isRecording}
          placeholder={isRecording ? 'Listening...' : placeholder}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-hearth-400 disabled:opacity-50"
        />

        {/* Voice button */}
        <button
          onClick={handleMicClick}
          disabled={disabled}
          className={`p-2 rounded-lg transition-colors ${
            isRecording
              ? 'bg-red-100 dark:bg-red-900/30 text-red-600 hover:bg-red-200 dark:hover:bg-red-800/40'
              : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-hearth-700'
          } disabled:opacity-30`}
          title={isRecording ? 'Stop recording' : 'Voice input'}
          aria-label={isRecording ? 'Stop recording' : 'Voice input'}
        >
          {isRecording ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={disabled}
          className="p-2 rounded-lg bg-hearth-600 hover:bg-hearth-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Send (Enter)"
          aria-label="Send"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
