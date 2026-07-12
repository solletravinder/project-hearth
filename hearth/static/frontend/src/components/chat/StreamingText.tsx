interface StreamingTextProps {
  text: string;
  isStreaming?: boolean;
}

export function StreamingText({ text, isStreaming = true }: StreamingTextProps) {
  return (
    <span className="whitespace-pre-wrap">
      {text}
      {isStreaming && (
        <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-hearth-500 animate-pulse align-middle" />
      )}
    </span>
  );
}
