import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { Video, ProcessingProgress, DetectionResponse, SegmentResponse } from '../types';
import { api } from '../api';
import { Loader2, Play, Check, Eye, EyeOff, Radio, Crosshair } from 'lucide-react';
import { cn } from '../lib/utils';
import { DetectionOverlay, DetectionStats } from './DetectionOverlay';
import { SegmentationOverlay } from './SegmentationOverlay';

interface VideoPlayerProps {
  video: Video | null;
  processingProgress: ProcessingProgress | null;
  onProcess: () => void;
  playerRef: React.RefObject<HTMLVideoElement | null>;
}

export function VideoPlayer({ video, processingProgress, onProcess, playerRef }: VideoPlayerProps) {
  const [detections, setDetections] = useState<DetectionResponse | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [showDetections, setShowDetections] = useState(true);
  const [videoSize, setVideoSize] = useState({ width: 0, height: 0 });
  const [autoDetect, setAutoDetect] = useState(false);
  const lastDetectTime = useRef(0);
  
  // Track mode state
  const [trackMode, setTrackMode] = useState(false);
  const [segment, setSegment] = useState<SegmentResponse | null>(null);
  const [isSegmenting, setIsSegmenting] = useState(false);
  const videoContainerRef = useRef<HTMLDivElement>(null);

  // Update video size when video loads
  useEffect(() => {
    const videoEl = playerRef.current;
    if (!videoEl) return;

    const updateSize = () => {
      setVideoSize({
        width: videoEl.clientWidth,
        height: videoEl.clientHeight
      });
    };

    videoEl.addEventListener('loadedmetadata', updateSize);
    videoEl.addEventListener('resize', updateSize);
    updateSize();

    return () => {
      videoEl.removeEventListener('loadedmetadata', updateSize);
      videoEl.removeEventListener('resize', updateSize);
    };
  }, [playerRef, video]);

  const handleDetect = useCallback(async () => {
    if (!video || !playerRef.current || isDetecting) return;

    setIsDetecting(true);
    try {
      const timestamp = playerRef.current.currentTime;
      const result = await api.detectObjects(video.id, timestamp);
      setDetections(result);
      setShowDetections(true);
      lastDetectTime.current = Date.now();
    } catch (error) {
      console.error('Detection failed:', error);
    } finally {
      setIsDetecting(false);
    }
  }, [video, playerRef, isDetecting]);

  // Continuous detection while video is playing
  useEffect(() => {
    if (!autoDetect || !video || !playerRef.current) return;

    const videoEl = playerRef.current;
    let animationFrame: number;

    const detectLoop = () => {
      if (!autoDetect) return;
      
      // Only detect if video is playing and enough time has passed (500ms)
      if (!videoEl.paused && Date.now() - lastDetectTime.current > 500) {
        handleDetect();
      }
      
      animationFrame = requestAnimationFrame(detectLoop);
    };

    detectLoop();

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [autoDetect, video, playerRef, handleDetect]);

  // Clear detections when video changes
  useEffect(() => {
    setDetections(null);
    setAutoDetect(false);
    setSegment(null);
    setTrackMode(false);
  }, [video?.id]);

  // Handle click for track mode
  const handleVideoClick = useCallback(async (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackMode || !video || !playerRef.current || isSegmenting) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    setIsSegmenting(true);
    try {
      const timestamp = playerRef.current.currentTime;
      const result = await api.segmentObject(video.id, timestamp, x, y);
      setSegment(result);
    } catch (error) {
      console.error('Segmentation failed:', error);
    } finally {
      setIsSegmenting(false);
    }
  }, [trackMode, video, playerRef, isSegmenting]);

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
       <div 
         ref={videoContainerRef}
         className={cn(
           "relative w-full aspect-video bg-black rounded-lg overflow-hidden shadow-sm group",
           trackMode && "cursor-crosshair"
         )}
         onClick={handleVideoClick}
       >
          <video 
            ref={playerRef}
            src={api.getVideoStreamUrl(video.id)}
            controls 
            className="w-full h-full object-contain"
          />
          
          {/* Segmentation overlay */}
          {segment && (
            <SegmentationOverlay
              segment={segment}
              videoWidth={videoSize.width}
              videoHeight={videoSize.height}
            />
          )}
          
          {/* Track mode indicator */}
          {trackMode && (
            <div className="absolute top-4 left-4 bg-cyan-500 text-white px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-2 shadow-lg">
              <Crosshair className="w-3.5 h-3.5" />
              TRACK MODE - Click on object to segment
              {isSegmenting && <Loader2 className="w-3 h-3 animate-spin" />}
            </div>
          )}
          {/* Detection overlay */}
          {showDetections && detections && (
            <DetectionOverlay
              detections={detections}
              videoWidth={videoSize.width}
              videoHeight={videoSize.height}
            />
          )}
          
          {isProcessing && (
            <div className="absolute inset-0 bg-zinc-900/90 backdrop-blur-sm flex flex-col items-center justify-center z-10 text-white">
               <div className="w-80 space-y-4">
                  <div className="flex items-center justify-center gap-2 mb-2">
                     <Loader2 className="w-5 h-5 animate-spin text-white" />
                     <span className="text-sm font-medium">Analyzing Video</span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                     <span>Frame {processingProgress.current_frame} / {processingProgress.total_frames}</span>
                     <span className="text-white font-semibold">{progressPercent}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                     <div 
                       className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-300 rounded-full" 
                       style={{ width: `${progressPercent}%` }} 
                     />
                  </div>
                  <p className="text-center text-xs text-zinc-400">
                    {processingProgress.message || 'Extracting frames and generating descriptions...'}
                  </p>
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
            
            {/* Detection stats */}
            <div className="mt-3">
              <DetectionStats detections={detections} isLoading={isDetecting} />
            </div>
          </div>

          <div className="flex gap-2">
            {/* Detect Objects Button */}
            <button
              onClick={handleDetect}
              disabled={isDetecting}
              className={cn(
                 "px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                 "bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:translate-y-0.5",
                 isDetecting && "opacity-50 cursor-not-allowed"
              )}
            >
               {isDetecting ? (
                 <Loader2 className="w-4 h-4 animate-spin" />
               ) : (
                 <Eye className="w-4 h-4" />
               )}
               Detect
            </button>
            
            {/* Live/Continuous Detection Toggle */}
            <button
              onClick={() => setAutoDetect(!autoDetect)}
              className={cn(
                 "px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                 autoDetect 
                   ? "bg-red-500 text-white hover:bg-red-600 shadow-sm"
                   : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              )}
            >
               <Radio className={cn("w-4 h-4", autoDetect && "animate-pulse")} />
               {autoDetect ? "LIVE" : "Live"}
            </button>
            
            {/* Track Mode Toggle */}
            <button
              onClick={() => {
                setTrackMode(!trackMode);
                if (!trackMode) setSegment(null);
              }}
              className={cn(
                 "px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                 trackMode 
                   ? "bg-cyan-500 text-white hover:bg-cyan-600 shadow-sm"
                   : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              )}
            >
               <Crosshair className="w-4 h-4" />
               {trackMode ? "TRACK" : "Track"}
            </button>
            {/* Toggle visibility */}
            {detections && (
              <button
                onClick={() => setShowDetections(!showDetections)}
                className={cn(
                  "p-2.5 rounded-lg transition-all",
                  showDetections 
                    ? "bg-zinc-200 text-zinc-700" 
                    : "bg-zinc-100 text-zinc-400"
                )}
                title={showDetections ? "Hide detections" : "Show detections"}
              >
                {showDetections ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
            )}

            {/* Process Button */}
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
    </div>
  );
}

