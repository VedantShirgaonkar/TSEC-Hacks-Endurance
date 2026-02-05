import React, { useState } from 'react';
import { Sparkles, ChevronDown } from 'lucide-react';

const ModelToggle = ({ isReasoningEnabled, onToggle, reasoningEffort, onEffortChange }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-2 py-1 rounded hover:bg-white/5 transition-colors text-xs font-medium ${isReasoningEnabled ? 'text-accent-primary' : 'text-text-tertiary'
                    }`}
            >
                <Sparkles size={14} className={isReasoningEnabled ? 'fill-current' : 'opacity-50'} />
                <span>{isReasoningEnabled ? 'Reasoning: On' : 'Reasoning: Off'}</span>
                <ChevronDown size={12} className="opacity-50" />
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute bottom-full left-0 mb-2 p-1 w-48 bg-bg-hover border border-border-subtle rounded-lg shadow-xl z-50 flex flex-col animate-fade-in">

                        <button
                            onClick={() => { onToggle(!isReasoningEnabled); setIsOpen(false); }}
                            className="flex items-center justify-between w-full px-3 py-2 hover:bg-white/5 rounded text-sm text-text-primary"
                        >
                            <span>Enable Reasoning</span>
                            {isReasoningEnabled && <div className="w-2 h-2 rounded-full bg-accent-primary" />}
                        </button>

                        {isReasoningEnabled && (
                            <div className="border-t border-white/5 mt-1 pt-1">
                                <span className="px-3 py-1 text-[10px] text-text-tertiary uppercase font-semibold block">Effort</span>
                                {['low', 'medium', 'high'].map(effort => (
                                    <button
                                        key={effort}
                                        onClick={() => onEffortChange(effort)}
                                        className={`w-full text-left px-3 py-1.5 text-xs capitalize hover:bg-white/5 ${reasoningEffort === effort ? 'text-accent-primary' : 'text-text-secondary'
                                            }`}
                                    >
                                        {effort}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default ModelToggle;
