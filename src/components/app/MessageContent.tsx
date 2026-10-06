'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageContentProps {
  content: string;
  onSelectCitation?: (citationId: string) => void;
}

export default function MessageContent({
  content,
  onSelectCitation,
}: MessageContentProps) {
  // Pre-process: replace [S1] or [W1] citations with markdown links [S1](#cite-S1)
  const processedContent = React.useMemo(() => {
    if (!content) return '';
    return content.replace(/\[(S\d+|W\d+)\]/g, '[$1](#cite-$1)');
  }, [content]);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none text-xs sm:text-sm leading-relaxed break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children, ...props }) => {
            if (href && href.startsWith('#cite-')) {
              const citationId = href.replace('#cite-', '');
              return (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    onSelectCitation?.(citationId);
                  }}
                  className="inline-flex items-center px-1.5 py-0.2 mx-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/25 border border-emerald-500/30 transition-colors align-baseline cursor-pointer"
                  title={`View source ${citationId}`}
                >
                  [{children}]
                </button>
              );
            }

            if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-600 dark:text-emerald-400 underline underline-offset-2 hover:opacity-80"
                  {...props}
                >
                  {children}
                </a>
              );
            }

            return <span>{children}</span>;
          },
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-xl border border-black/10 dark:border-white/10">
              <table className="w-full text-left text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="p-2 border-b border-black/10 dark:border-white/10 font-bold bg-black/5 dark:bg-white/5 font-mono text-[11px]">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="p-2 border-b border-black/5 dark:border-white/5 text-xs">
              {children}
            </td>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/10 text-emerald-600 dark:text-emerald-400 font-mono text-[11px]"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}
