import type { Message, Citation } from '@/types';
import { formatDate } from '@/utils/format';

interface MessageBubbleProps {
  message: Message;
}

const citationColors: Record<string, string> = {
  green: 'bg-green-100 text-green-800 border-green-200',
  amber: 'bg-amber-100 text-amber-800 border-amber-200',
  red: 'bg-red-100 text-red-800 border-red-200',
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center py-2">
        <span className="text-xs text-gray-400 dark:text-gray-500 italic">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-2`}>
      <div
        className={`
          max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
          ${
            isUser
              ? 'bg-hearth-600 text-white rounded-br-md'
              : 'bg-white dark:bg-hearth-800 border border-gray-200 dark:border-hearth-700 text-gray-900 dark:text-gray-100 rounded-bl-md'
          }
        `}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.citations && message.citations.length > 0 && (
          <div className={`mt-3 pt-2 border-t ${isUser ? 'border-hearth-500' : 'border-gray-200 dark:border-hearth-600'}`}>
            <p className="text-xs font-medium mb-1 opacity-70">Sources</p>
            <div className="space-y-1">
              {message.citations.map((c: Citation) => (
                <div
                  key={c.id}
                  className={`
                    text-xs rounded px-2 py-1 border
                    ${citationColors[c.color] || citationColors.amber}
                  `}
                >
                  <span className="font-medium">{c.doc_title}</span>
                  {c.verified && (
                    <span className="ml-1" title="Verified">&#10003;</span>
                  )}
                  <span className="ml-1 opacity-60">
                    ({(c.score * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className={`mt-1 text-xs opacity-50 ${isUser ? 'text-white/60' : 'text-gray-400'}`}>
          {message.token_count != null && `${message.token_count} tokens`}
          {message.token_count != null && message.generation_ms != null && ' · '}
          {message.generation_ms != null && `${message.generation_ms}ms`}
          {(message.token_count != null || message.generation_ms != null) && ' · '}
          {formatDate(message.created_at)}
        </div>
      </div>
    </div>
  );
}
