import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import IngestModal from './components/IngestModal';
import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, Settings, Upload } from 'lucide-react';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);

  return (
    <div className="w-full h-screen flex bg-bg-primary text-text-primary relative overflow-hidden">

      {/* Sidebar */}
      <div
        className={`${isSidebarOpen ? 'w-[260px] translate-x-0' : 'w-0 -translate-x-full'
          } bg-bg-secondary flex flex-col h-full transition-all duration-300 ease-in-out border-r border-border-subtle absolute md:relative z-20`}
      >
        <div className="p-3 flex-1 overflow-y-auto custom-scrollbar">
          {/* New Chat Button */}
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-3 px-3 py-3 w-full rounded-md border border-white/20 hover:bg-white/5 transition-colors text-sm text-text-primary mb-2"
          >
            <Plus size={16} />
            New chat
          </button>

          {/* Upload Document Button */}
          <button
            onClick={() => setIsIngestModalOpen(true)}
            className="flex items-center gap-3 px-3 py-3 w-full rounded-md border border-accent-primary/30 hover:bg-accent-primary/10 transition-colors text-sm text-accent-primary mb-4"
          >
            <Upload size={16} />
            Upload Document
          </button>

          {/* History Section (Simulated) */}
          <div className="flex flex-col gap-2">
            <span className="px-3 text-xs font-medium text-text-tertiary py-2">Today</span>
            <button className="flex items-center gap-3 px-3 py-3 w-full rounded-md hover:bg-white/5 transition-colors text-sm text-text-secondary hover:text-text-primary truncate text-left group">
              <MessageSquare size={16} className="text-text-tertiary group-hover:text-text-primary placeholder:opacity-50" />
              <span className="truncate">RTI Query Analysis</span>
            </button>
          </div>
        </div>

        {/* User / Settings Footer */}
        <div className="p-3 border-t border-border-subtle">
          <button className="flex items-center gap-3 px-3 py-3 w-full rounded-md hover:bg-white/5 transition-colors text-sm text-text-primary">
            <div className="w-6 h-6 rounded-sm bg-accent-secondary/80 flex items-center justify-center text-[10px] font-bold text-white">
              U
            </div>
            <div className="font-medium">User</div>
            <Settings size={16} className="ml-auto text-text-tertiary" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative min-w-0 bg-bg-primary">

        {/* Mobile Sidebar Toggle */}
        <div className="absolute top-3 left-3 z-30 md:hidden">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-md text-text-tertiary hover:text-text-primary hover:bg-white/10 transition-colors"
          >
            {isSidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
          </button>
        </div>

        {/* Desktop Toggle (Floating) */}
        <div className="absolute top-1/2 -left-3 z-30 hidden md:block">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="group p-1 bg-bg-primary border border-border-subtle rounded-full text-text-tertiary hover:text-text-primary transition-all hover:scale-110 shadow-md"
            title="Toggle Sidebar"
          >
            {isSidebarOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
          </button>
        </div>

        {/* Header - Minimal */}
        <header className="h-12 border-b border-white/5 flex items-center justify-center md:justify-between px-4 bg-bg-primary">
          <div className="md:hidden" />
          <div className="flex items-center gap-2 opacity-80">
            <span className="text-sm font-medium text-text-secondary">RTI AI</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-accent-secondary/10 text-accent-secondary font-mono border border-accent-secondary/20">v1.0</span>
          </div>
          <div className="w-8 md:w-auto" />
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden relative">
          <ChatInterface />
        </div>
      </div>

      {/* Ingest Modal */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
      />
    </div>
  );
}

export default App;
