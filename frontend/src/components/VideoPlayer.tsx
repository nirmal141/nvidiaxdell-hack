import React from 'react';
import type { Video, ProcessingProgress } from '../types';
import { api } from '../api';
import { Loader2, Play, Check } from 'lucide-react';
import { cn } from '../lib/utils';

interface VideoPlayerProps {
  video: Video | null;
  processingProgress: ProcessingProgress | null;
  onProcess: () => void;
  playerRef: React.RefObject<HTMLVideoElement | null>;
}

export function VideoPlayer({ video, processingProgress, onProcess, playerRef }: VideoPlayerProps) {
  if (!video) {
    return (
      <div className="h-full flex items-center justify-center bg-zinc-50 border border-zinc-200 border-dashed rounded-xl">
        <div className="text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                <Play className="w-6 h-6 text-zinc-300 ml-1" />
            </div>
            <p className="text-zinc-500 font-medium">No video selected</p>
        </div>
      </div>
    );
  }

  const isProcessing = processingProgress?.status === 'processing';
  const progressPercent = processingProgress && processingProgress.total_frames > 0
    ? Math.round((processingProgress.current_frame / processingProgress.total_frames) * 100)
    : 0;

  return (
    <div className="flex flex-col gap-6 h-full">
       <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden shadow-sm group">
          <video 
            ref={playerRef}
            src={api.getVideoStreamUrl(video.id)}
            controls 
            className="w-full h-full object-contain"
          />
          
          {isProcessing && (
            <div className="absolute inset-0 bg-zinc-900/90 backdrop-blur-sm flex flex-col items-center justify-center z-10 text-white">
               <div className="w-64 space-y-4">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                     <span>PROCESSING</span>
                     <span>{progressPercent}%</span>
                  </div>
                  <div className="h-0.5 w-full bg-zinc-800">
                     <div className="h-full bg-white transition-all duration-300" style={{ width: `${progressPercent}%` }} />
                  </div>
                  <p className="text-center text-xs text-zinc-500 animate-pulse">{processingProgress.message}</p>
               </div>
            </div>
          )}
       </div>

       <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-900 tracking-tight">{video.name}</h1>
            <div className="flex items-center gap-2 mt-2">
               <span className={cn(
                 "inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider",
                 video.status === 'completed' ? "bg-emerald-100 text-emerald-800" : 
                 video.status === 'failed' ? "bg-red-100 text-red-800" : 
                 "bg-zinc-100 text-zinc-600"
               )}>
                  {video.status === 'completed' && <Check className="w-3 h-3" />}
                  {video.status}
               </span>
               <span className="text-xs text-zinc-400 font-mono">
                  ID: {video.id}
               </span>
            </div>
          </div>

          <button
            onClick={onProcess}
            disabled={video.status === 'processing' || video.status === 'completed'}
            className={cn(
               "px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
               video.status === 'completed' 
                 ? "bg-zinc-100 text-zinc-400 cursor-not-allowed"
                 : "bg-zinc-900 text-white hover:bg-zinc-800 shadow-sm active:translate-y-0.5"
            )}
          >
             {video.status === 'processing' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
             {video.status === 'completed' ? 'Analyzed' : 'Start Analysis'}
          </button>
       </div>
    </div>
  );
}
