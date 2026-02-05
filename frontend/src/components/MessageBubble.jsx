import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';
import ReasoningTrace from './ReasoningTrace';
import SourceCitations from './SourceCitations';

const MessageBubble = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`w-full py-6 md:py-8 border-b border-black/5 dark:border-white/5 ${isUser ? 'bg-transparent' : 'bg-transparent'}`}>
            <div className="max-w-3xl mx-auto w-full flex gap-4 md:gap-6 px-4">

                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-sm flex items-center justify-center ${isUser
                        ? 'bg-accent-secondary text-white' // Indigo
                        : 'bg-accent-primary text-white' // Green
                    }`}>
                    {isUser ? <User size={18} /> : <Bot size={18} />}
                </div>

                {/* Content Area */}
                <div className="flex-1 space-y-4 overflow-hidden min-w-0">

                    {/* Main Text */}
                    <div className="prose prose-invert prose-p:leading-relaxed prose-pre:bg-bg-secondary prose-pre:border prose-pre:border-border-subtle max-w-none text-[15px] text-text-primary
              prose-headings:font-semibold prose-h3:text-lg prose-h4:text-base
              prose-table:border-collapse prose-table:border prose-table:border-border-subtle prose-table:bg-bg-hover prose-table:rounded-lg prose-table:overflow-hidden 
              prose-th:bg-white/5 prose-th:p-3 prose-th:text-left prose-th:font-medium prose-th:border-b prose-th:border-border-subtle
              prose-td:p-3 prose-td:border-b prose-td:border-white/5 last:prose-td:border-0">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                table: ({ node, ...props }) => <div className="overflow-x-auto my-4 rounded-lg border border-border-subtle"><table className="w-full text-sm text-left" {...props} /></div>
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    </div>

                    {/* Reasoning Trace (Bot only) */}
                    {!isUser && message.reasoning_trace && (
                        <div className="pt-2">
                            <ReasoningTrace content={message.reasoning_trace} />
                        </div>
                    )}

                    {/* Sources (Bot only) */}
                    {!isUser && message.sources && message.sources.length > 0 && (
                        <SourceCitations sources={message.sources} />
                    )}

                    {/* Metadata Footer */}
                    {!isUser && (
                        <div className="flex items-center gap-3 pt-1">
                            {message.model && (
                                <span className="text-[10px] uppercase tracking-widest text-text-tertiary font-medium">
                                    {message.model}
                                </span>
                            )}
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default MessageBubble;
