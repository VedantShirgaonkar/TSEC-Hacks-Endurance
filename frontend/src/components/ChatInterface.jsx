import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, StopCircle } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ModelToggle from './ModelToggle';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hello! I'm your RTI Assistant. I can help you find information from official documents.\n\nTry asking me about specific policies or enable **Reasoning** for deeper analysis.",
            timestamp: new Date().toISOString(),
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isReasoningEnabled, setIsReasoningEnabled] = useState(false);
    const [reasoningEffort, setReasoningEffort] = useState('medium');
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [inputValue]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
        setIsLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage.content,
                    enable_reasoning: isReasoningEnabled,
                    reasoning_effort: reasoningEffort,
                }),
            });

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();

            const botMessage = {
                id: data.session_id + Date.now(),
                role: 'assistant',
                content: data.response,
                sources: data.sources,
                reasoning_trace: data.reasoning_trace,
                model: data.model_used,
                timestamp: data.timestamp,
            };

            setMessages(prev => [...prev, botMessage]);

        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: "I apologize, but I encountered an error. Please ensure the backend is reachable.",
                timestamp: new Date().toISOString(),
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    return (
        <div className="flex flex-col h-full relative scroll-smooth bg-bg-primary">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="flex flex-col pb-48 pt-4">
                    {messages.map((msg) => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))}

                    {isLoading && (
                        <div className="w-full py-6 md:py-8">
                            <div className="max-w-3xl mx-auto px-4 flex gap-4 md:gap-6">
                                <div className="flex-shrink-0 w-8 h-8 rounded-sm bg-accent-primary flex items-center justify-center text-white">
                                    <Loader2 size={18} className="animate-spin" />
                                </div>
                                <div className="flex items-center gap-2 pt-1 text-text-tertiary">
                                    <span className="shimmer text-sm font-medium">Thinking...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-bg-primary via-bg-primary to-transparent pt-10 pb-6 px-4 z-10">
                <div className="max-w-3xl mx-auto w-full relative">

                    {/* Main Input Box */}
                    <div className="relative flex flex-col w-full p-3 bg-bg-hover border border-border-subtle rounded-xl shadow-lg focus-within:border-gray-500/50 transition-colors">

                        {/* Model & Reasoning Toggles */}
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/5">
                            <ModelToggle
                                isReasoningEnabled={isReasoningEnabled}
                                onToggle={setIsReasoningEnabled}
                                reasoningEffort={reasoningEffort}
                                onEffortChange={setReasoningEffort}
                            />
                        </div>

                        <textarea
                            ref={textareaRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Send a message..."
                            className="w-full bg-transparent text-text-primary placeholder:text-text-tertiary resize-none outline-none max-h-[200px] overflow-y-auto text-[15px] leading-relaxed custom-scrollbar"
                            rows={1}
                            disabled={isLoading}
                        />

                        <div className="absolute bottom-3 right-3">
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isLoading}
                                className={`p-1.5 rounded-md transition-all ${!inputValue.trim() || isLoading
                                    ? 'bg-transparent text-text-tertiary cursor-not-allowed'
                                    : 'bg-accent-primary text-white hover:bg-opacity-90 shadow-sm'
                                    }`}
                            >
                                {isLoading ? <StopCircle size={16} /> : <Send size={16} />}
                            </button>
                        </div>
                    </div>

                    <div className="text-center mt-3">
                        <p className="text-[10px] text-text-tertiary opacity-80">
                            RTI AI uses advanced reasoning. Responses may take a moment.
                        </p>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
