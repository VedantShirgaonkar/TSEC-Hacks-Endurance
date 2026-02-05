import React, { useState } from 'react';
import { BrainCircuit, ChevronDown, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ReasoningTrace = ({ content }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!content) return null;

    return (
        <div className="mt-2 mb-2 w-full max-w-full">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-yellow-500/5 hover:bg-yellow-500/10 border border-yellow-500/10 group transition-colors text-yellow-200/80"
            >
                <div className="flex items-center gap-2">
                    <BrainCircuit size={16} className="text-yellow-500/80" />
                    <span className="text-sm font-medium">Thought Process</span>
                </div>
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>

            {isExpanded && (
                <div className="mt-1 p-3 rounded-lg bg-bg-secondary border border-yellow-500/5 text-yellow-100/70 text-sm font-mono leading-relaxed overflow-x-auto custom-scrollbar">
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>
            )}
        </div>
    );
};

export default ReasoningTrace;
