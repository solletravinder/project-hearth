import { useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { StreamingText } from './StreamingText';
import { Spinner } from '@/components/common/Spinner';
import { EmptyState } from '@/components/common/EmptyState';

export function ChatView() {
  const {
    messages,
    isStreaming,
    streamBuffer,
    statusMessage,
    error,
    sendMessage,
  } = useChat();

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamBuffer]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center flex-col gap-4">
          <EmptyState
            title="Start a conversation"
            description="Ask questions, upload documents, or research any topic."
          />
          {error && (
            <div className="max-w-md w-full px-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-2 text-sm text-red-700 dark:text-red-400 text-center">
                {error}
              </div>
            </div>
          )}
        </div>
        <ChatInput onSend={sendMessage} />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 overflow-y-auto py-4 space-y-1">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isStreaming && (
          <>
            {statusMessage && (
              <div className="flex justify-center py-2">
                <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
                  <Spinner size="sm" />
                  {statusMessage}
                </span>
              </div>
            )}
            {streamBuffer && (
              <div className="flex justify-start px-4 py-2">
                <div className="max-w-[75%] rounded-2xl rounded-bl-md px-4 py-2.5 text-sm leading-relaxed bg-white dark:bg-hearth-800 border border-gray-200 dark:border-hearth-700 text-gray-900 dark:text-gray-100">
                  <StreamingText text={streamBuffer} />
                </div>
              </div>
            )}
          </>
        )}

        {error && (
          <div className="flex justify-center py-2 px-4">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-2 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
