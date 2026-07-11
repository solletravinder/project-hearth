interface StreamingTextProps {
  text: string;
}

export function StreamingText({ text }: StreamingTextProps) {
  return <span className="whitespace-pre-wrap">{text}</span>;
}
