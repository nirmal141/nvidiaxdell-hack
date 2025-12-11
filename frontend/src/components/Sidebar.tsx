import React, { useRef, useState } from 'react';
import { Upload, RefreshCw, Plus, Trash2, Loader2, Zap, Square } from 'lucide-react';
import type { Video } from '../types';
import { cn } from '../lib/utils';

interface SidebarProps {
  videos: Video[];
  currentVideo: Video | null;
  onSelectVideo: (video: Video) => void;
  onUpload: (file: File) => void;
  onRefresh: () => void;
  onDeleteVideo: (videoId: string) => void;
  onProcessVideo?: (videoId: string) => void;
  onStopProcessing?: (videoId: string) => void;
  isUploading: boolean;
  onGoToSearch?: () => void;
  viewMode?: 'search' | 'video';
}

export function Sidebar({ 
  videos, 
  currentVideo, 
  onSelectVideo, 
  onUpload, 
  onRefresh, 
  onDeleteVideo, 
  onProcessVideo,
  onStopProcessing,
  isUploading, 
  onGoToSearch 
}: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [hoveredVideo, setHoveredVideo] = useState<string | null>(null);

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

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Ready';
      case 'processing': return 'Processing';
      case 'failed': return 'Failed';
      default: return 'Pending';
    }
  };

  const isUnprocessed = (video: Video) => {
    return !video.status || video.status === 'pending';
  };

  return (
    <div className="w-[280px] h-full bg-white border-r border-zinc-200 flex flex-col">
      {/* Header */}
      <div className="h-14 flex items-center px-5 border-b border-zinc-100">
        <button onClick={onGoToSearch} className="flex items-center gap-2.5 hover:opacity-70 transition-opacity">
          <div className="w-7 h-7 bg-zinc-900 rounded-lg flex items-center justify-center">
            <div className="w-2 h-2 bg-white rounded-full" />
          </div>
          <span className="font-semibold text-zinc-900 text-[15px]">Sentio</span>
        </button>
      </div>

      {/* Upload Button */}
      <div className="p-4">
        <button 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full h-9 border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 rounded-lg transition-all flex items-center justify-center gap-2 text-sm font-medium disabled:opacity-50"
        >
          {isUploading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Plus className="w-4 h-4" />
          )}
          <span>{isUploading ? 'Uploading...' : 'Add Video'}</span>
        </button>
        <input 
          type="file" 
          ref={fileInputRef}
          className="hidden" 
          accept="video/*"
          onChange={handleFileChange}
        />
      </div>

      {/* Library Header */}
      <div className="px-5 py-2 flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Library</span>
        <button 
          onClick={onRefresh} 
          className="p-1 hover:bg-zinc-100 rounded transition-colors text-zinc-400 hover:text-zinc-600"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Video List */}
      <div className="flex-1 overflow-y-auto px-2">
        <div className="space-y-0.5">
          {videos.length === 0 ? (
            <div className="text-center py-12 px-4">
              <div className="w-12 h-12 bg-zinc-100 rounded-full flex items-center justify-center mx-auto mb-3 text-zinc-300">
                <Upload className="w-5 h-5" />
              </div>
              <p className="text-sm text-zinc-400">No videos yet</p>
            </div>
          ) : (
            videos.map(video => {
              const unprocessed = isUnprocessed(video);
              const isHovered = hoveredVideo === video.id;
              const isSelected = currentVideo?.id === video.id;
              const isProcessing = video.status === 'processing';
              const isFailed = video.status === 'failed';

              return (
                <div 
                  key={video.id}
                  onMouseEnter={() => setHoveredVideo(video.id)}
                  onMouseLeave={() => setHoveredVideo(null)}
                  className={cn(
                    "relative rounded-lg transition-all group",
                    isSelected 
                      ? "bg-zinc-100" 
                      : "hover:bg-zinc-50",
                    unprocessed && "opacity-50 hover:opacity-100"
                  )}
                >
                  <button
                    onClick={() => onSelectVideo(video)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 text-left"
                  >
                    {/* Status Dot */}
                    <div className={cn(
                      "w-2 h-2 rounded-full shrink-0",
                      video.status === 'completed' ? "bg-emerald-500" :
                      video.status === 'processing' ? "bg-blue-500 animate-pulse" :
                      video.status === 'failed' ? "bg-red-500" : 
                      "bg-zinc-300"
                    )} />

                    <div className="flex-1 min-w-0">
                      <div className={cn(
                        "text-sm font-medium truncate",
                        isSelected ? "text-zinc-900" : "text-zinc-700"
                      )}>
                        {video.name}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-zinc-400 font-mono">
                          {formatDuration(video.duration)}
                        </span>
                        <span className="text-zinc-300">•</span>
                        <span className={cn(
                          "text-[10px] font-medium",
                          video.status === 'completed' ? "text-emerald-600" :
                          video.status === 'processing' ? "text-blue-600" :
                          video.status === 'failed' ? "text-red-600" :
                          "text-zinc-400"
                        )}>
                          {getStatusLabel(video.status)}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Action Buttons - Show on hover */}
                  <div className={cn(
                    "absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 transition-opacity",
                    isHovered ? "opacity-100" : "opacity-0"
                  )}>
                    {/* Stop Button - for processing videos */}
                    {isProcessing && onStopProcessing && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onStopProcessing(video.id);
                        }}
                        className="p-1.5 bg-red-100 hover:bg-red-200 rounded text-red-600 transition-all"
                        title="Stop Processing"
                      >
                        <Square className="w-3 h-3" fill="currentColor" />
                      </button>
                    )}

                    {/* Process Button - for unprocessed or failed */}
                    {(unprocessed || isFailed) && !isProcessing && onProcessVideo && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onProcessVideo(video.id);
                        }}
                        className="p-1.5 bg-blue-100 hover:bg-blue-200 rounded text-blue-600 transition-all"
                        title="Analyze Video"
                      >
                        <Zap className="w-3 h-3" />
                      </button>
                    )}

                    {/* Delete Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('Delete this video?')) {
                          onDeleteVideo(video.id);
                        }
                      }}
                      className="p-1.5 hover:bg-red-100 rounded text-zinc-400 hover:text-red-600 transition-all"
                      title="Delete"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-zinc-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-zinc-200 rounded-full flex items-center justify-center text-xs font-medium text-zinc-600">
            U
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium text-zinc-700">Workspace</div>
          </div>
        </div>
      </div>
    </div>
  );
}
