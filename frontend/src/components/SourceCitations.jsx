import React from 'react';
import { BookOpen, FileText } from 'lucide-react';

const SourceCitations = ({ sources }) => {
    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-3 pt-3 border-t border-border-subtle flex flex-col gap-2">
            <h4 className="flex items-center gap-1.5 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                <BookOpen size={12} />
                Sources
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {sources.map((source, idx) => (
                    <div
                        key={idx}
                        className="flex flex-col gap-1 p-2.5 rounded-lg bg-bg-hover hover:bg-white/5 border border-border-subtle hover:border-white/10 transition-colors cursor-default"
                    >
                        <div className="flex items-center gap-2 text-text-secondary">
                            <FileText size={14} />
                            <span className="text-xs font-medium truncate" title={source.source}>
                                {source.source.split('/').pop()}
                            </span>
                        </div>
                        <p className="text-[11px] text-text-tertiary line-clamp-2 leading-tight">
                            {source.content}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SourceCitations;
