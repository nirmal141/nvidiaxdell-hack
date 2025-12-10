import React, { useRef } from 'react';
import { Upload, RefreshCw, Plus, Trash2 } from 'lucide-react';
import type { Video } from '../types';
import { cn } from '../lib/utils';

interface SidebarProps {
  videos: Video[];
  currentVideo: Video | null;
  onSelectVideo: (video: Video) => void;
  onUpload: (file: File) => void;
  onRefresh: () => void;
  onDeleteVideo: (videoId: string) => void;
  isUploading: boolean;
}

export function Sidebar({ videos, currentVideo, onSelectVideo, onUpload, onRefresh, onDeleteVideo, isUploading }: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      onUpload(e.target.files[0]);
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '--:--';
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-[280px] h-full bg-zinc-50 border-r border-zinc-200 flex flex-col">
      {/* Header */}
      <div className="h-16 flex items-center px-6 border-b border-zinc-100">
        <div className="w-5 h-5 bg-zinc-900 rounded-lg flex items-center justify-center mr-3">
            <div className="w-2 h-2 bg-white rounded-full" />
        </div>
        <span className="font-semibold text-zinc-900 tracking-tight">Visionary</span>
      </div>

      {/* Upload Action */}
      <div className="p-4">
        <button 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full h-10 border border-zinc-200 bg-white hover:bg-zinc-50 hover:border-zinc-300 text-zinc-700 rounded-lg transition-all flex items-center justify-center gap-2 text-sm font-medium shadow-sm active:translate-y-0.5 disabled:opacity-50"
        >
           {isUploading ? (
             <RefreshCw className="w-4 h-4 animate-spin" />
           ) : (
             <Plus className="w-4 h-4" />
           )}
           <span>{isUploading ? 'Uploading...' : 'New Video'}</span>
        </button>
        <input 
          type="file" 
          ref={fileInputRef}
          className="hidden" 
          accept="video/*"
          onChange={handleFileChange}
        />
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2">
        <div className="px-4 py-2 flex items-center justify-between text-xs font-medium text-zinc-400 uppercase tracking-wider">
          <span>Library</span>
          <button onClick={onRefresh} className="hover:text-zinc-700 transition-colors">
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
        
        <div className="space-y-0.5 mt-1">
          {videos.length === 0 ? (
             <div className="text-center py-12 px-4">
                <div className="w-12 h-12 bg-zinc-100 rounded-full flex items-center justify-center mx-auto mb-3 text-zinc-300">
                   <Upload className="w-5 h-5" />
                </div>
                <p className="text-sm text-zinc-500">No videos yet</p>
             </div>
          ) : (
            videos.map(video => (
              <div 
                key={video.id}
                className={cn(
                  "w-full flex items-center group relative rounded-lg transition-all",
                  currentVideo?.id === video.id 
                    ? "bg-white shadow-sm border border-zinc-200" 
                    : "hover:bg-zinc-100/50"
                )}
              >
                  <button
                    onClick={() => onSelectVideo(video)}
                    className="flex-1 flex items-center gap-3 px-4 py-3 text-left w-full min-w-0"
                  >
                    {/* Minimal Status Dot */}
                    <div className={cn(
                        "w-2 h-2 rounded-full shrink-0",
                        video.status === 'completed' ? "bg-emerald-500" :
                        video.status === 'processing' ? "bg-blue-500 animate-pulse" :
                        video.status === 'failed' ? "bg-red-500" : "bg-zinc-300"
                    )} />

                    <div className="flex-1 min-w-0">
                        <div className={cn("text-sm font-medium truncate", currentVideo?.id === video.id ? "text-zinc-900" : "text-zinc-700")}>
                        {video.name}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-zinc-400 font-mono">{formatDuration(video.duration)}</span>
                        </div>
                    </div>
                  </button>

                  <button
                    onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this video?')) {
                            onDeleteVideo(video.id);
                        }
                    }}
                    className="absolute right-2 opacity-0 group-hover:opacity-100 p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-all"
                    title="Delete video"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
              </div>
            ))
          )}
        </div>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-zinc-100">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 bg-zinc-200 rounded-full flex items-center justify-center text-xs font-bold text-zinc-600">
              U
           </div>
           <div className="flex-1">
              <div className="text-xs font-medium text-zinc-900">User Workspace</div>
              <div className="text-[10px] text-zinc-400">Pro Plan</div>
           </div>
        </div>
      </div>
    </div>
  );
}
