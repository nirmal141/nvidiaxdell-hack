import React, { useRef, useState } from 'react';
import { Send, Bot, Play, Sparkles } from 'lucide-react';
import type { ChatMessage } from '../types';
import { cn } from '../lib/utils';

interface ChatProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onSeek: (timestamp: number) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  "Summarize the content",
  "Who are the speakers?",
  "List key takeaways"
];

export function Chat({ messages, onSendMessage, onSeek, disabled }: ChatProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const formatTimestamp = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };
  
  const renderContent = (content: string) => {
    const parts = content.split(/(\[\d{1,2}:\d{2}\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d{1,2}):(\d{2})\]$/);
      if (match) {
        const seconds = parseInt(match[1]) * 60 + parseInt(match[2]);
        return (
          <button 
            key={i}
            onClick={() => onSeek(seconds)}
            className="inline-flex items-center gap-0.5 text-zinc-900 border-b border-zinc-300 hover:border-zinc-900 cursor-pointer font-mono font-medium mx-1 text-xs transition-colors"
          >
            {match[1]}:{match[2]}
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.05)] border border-zinc-100 overflow-hidden">
      <div className="h-14 px-5 border-b border-zinc-100 flex items-center justify-between">
         <div className="flex items-center gap-2">
           <Sparkles className="w-4 h-4 text-zinc-900" />
           <span className="font-semibold text-zinc-800 text-sm">Assistant</span>
         </div>
         <div className="text-xs text-zinc-400">GPT-4o Model</div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-8" ref={scrollRef}>
        {messages.length === 0 ? (
           <div className="h-full flex flex-col items-center justify-center">
              <div className="w-12 h-12 bg-zinc-50 rounded-xl flex items-center justify-center mb-4">
                 <Bot className="w-6 h-6 text-zinc-300" />
              </div>
              <h4 className="text-zinc-900 font-medium mb-1">How can I help?</h4>
              <p className="text-zinc-400 text-sm mb-6">Ask questions about the video content.</p>
              
              <div className="flex flex-wrap gap-2 justify-center max-w-sm">
                 {SUGGESTIONS.map(s => (
                   <button 
                     key={s}
                     onClick={() => !disabled && onSendMessage(s)}
                     disabled={disabled}
                     className="px-3 py-1.5 text-xs font-medium bg-zinc-50 border border-zinc-200 text-zinc-600 rounded-md hover:bg-zinc-100 hover:text-zinc-900 transition-colors disabled:opacity-50"
                   >
                     {s}
                   </button>
                 ))}
              </div>
           </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={cn("flex gap-4", msg.role === 'user' ? "flex-row-reverse" : "")}>
               <div className={cn(
                 "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-medium",
                 msg.role === 'user' ? "bg-zinc-900 text-white" : "bg-zinc-100 text-zinc-600"
               )}>
                  {msg.role === 'user' ? 'U' : <Bot className="w-4 h-4" />}
               </div>
               
               <div className={cn(
                 "max-w-[90%] text-sm leading-7",
                 msg.role === 'user' ? "text-right" : "text-zinc-700"
               )}>
                  <div className="whitespace-pre-wrap">{renderContent(msg.content)}</div>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 grid gap-2">
                       {msg.sources.map((source, i) => (
                          <button 
                            key={i}
                            onClick={() => onSeek(source.timestamp)}
                            className="flex items-start text-left gap-3 p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors group"
                          >
                             <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-zinc-900 bg-white border border-zinc-200 px-1.5 py-0.5 rounded shadow-sm shrink-0 group-hover:border-zinc-300 transition-colors">
                                <Play className="w-2.5 h-2.5" />
                                {formatTimestamp(source.timestamp)}
                             </div>
                             <div className="text-xs text-zinc-500 line-clamp-2 leading-relaxed">
                                {source.description}
                             </div>
                          </button>
                       ))}
                    </div>
                  )}
               </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 bg-white border-t border-zinc-100">
        <form onSubmit={handleSubmit} className="relative">
           <input 
             type="text" 
             value={input}
             onChange={(e) => setInput(e.target.value)}
             disabled={disabled}
             placeholder={disabled ? "Processing video..." : "Ask a question..."}
             className="w-full pl-4 pr-12 py-3 bg-zinc-50 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-zinc-900 focus:bg-white transition-all placeholder:text-zinc-400 disabled:opacity-50 disabled:cursor-not-allowed"
           />
           <button 
             type="submit"
             disabled={!input.trim() || disabled}
             className="absolute right-2 top-2 p-1.5 bg-zinc-900 text-white rounded-md hover:bg-zinc-800 disabled:opacity-50 disabled:bg-zinc-200 transition-colors"
           >
              <Send className="w-3.5 h-3.5" />
           </button>
        </form>
      </div>
    </div>
  );
}
