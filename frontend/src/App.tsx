import { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { VideoPlayer } from './components/VideoPlayer';
import { Chat } from './components/Chat';
import { Dashboard } from './components/Dashboard';
import type { Video, ChatMessage, ProcessingProgress } from './types';
import { api } from './api';
import { Toaster, toast } from 'sonner';

type ViewMode = 'search' | 'video';

function App() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('search');
  const [pendingSeek, setPendingSeek] = useState<number | null>(null);
  const videoPlayerRef = useRef<HTMLVideoElement>(null);

  const loadVideos = async () => {
    try {
      const data = await api.fetchVideos();
      setVideos(data.videos);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load videos');
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let pingInterval: ReturnType<typeof setInterval> | null = null;
    let isMounted = true;

    const connect = () => {
      if (!isMounted || !currentVideo?.id) return;
      if (currentVideo.status !== 'processing' && processingProgress?.status !== 'processing') return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/progress/${currentVideo.id}`;
      
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // Start sending pings to keep connection alive
        pingInterval = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 15000); // Ping every 15 seconds
      };

      ws.onmessage = (event) => {
        // Ignore pong responses
        if (event.data === 'pong' || event.data === 'ping') return;

        try {
          const progress: ProcessingProgress = JSON.parse(event.data);
          setProcessingProgress(progress);
          
          if (progress.status === 'completed') {
            toast.success('Analysis complete');
            loadVideos();
            setCurrentVideo(prev => prev ? { ...prev, status: 'completed' } : null);
            setProcessingProgress(null);
          } else if (progress.status === 'failed') {
            toast.error('Analysis failed');
            loadVideos();
            setCurrentVideo(prev => prev ? { ...prev, status: 'failed' } : null);
            setProcessingProgress(null);
          }
        } catch (e) {
          // Ignore parse errors for non-JSON messages
        }
      };

      ws.onclose = () => {
        if (pingInterval) clearInterval(pingInterval);
        // Auto-reconnect if still processing
        if (isMounted && (currentVideo?.status === 'processing' || processingProgress?.status === 'processing')) {
          reconnectTimeout = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => {
        // Will trigger onclose
      };
    };

    connect();

    return () => {
      isMounted = false;
      if (pingInterval) clearInterval(pingInterval);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, [currentVideo?.id, currentVideo?.status, processingProgress?.status]);

  // Handle pending seek when video is ready
  useEffect(() => {
    if (pendingSeek !== null && videoPlayerRef.current) {
      const timer = setTimeout(() => {
        if (videoPlayerRef.current) {
          videoPlayerRef.current.currentTime = pendingSeek;
          videoPlayerRef.current.play();
          setPendingSeek(null);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [pendingSeek, currentVideo]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const res = await api.uploadVideo(file);
      if (res.success) {
        toast.success('Uploaded successfully');
        await loadVideos();
        setCurrentVideo(res.video); 
        setViewMode('video');
      } else {
        toast.error('Upload failed');
      }
    } catch (e) {
      console.error(e);
      toast.error('Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteVideo = async (videoId: string) => {
    try {
      await api.deleteVideo(videoId);
      toast.success('Video deleted');
      if (currentVideo?.id === videoId) {
        setCurrentVideo(null);
        setChatMessages([]);
        setProcessingProgress(null);
        setViewMode('search');
      }
      loadVideos();
    } catch (e) {
      console.error(e);
      toast.error('Failed to delete video');
    }
  };

  const handleProcess = async () => {
    if (!currentVideo) return;
    try {
      await api.processVideo(currentVideo.id);
      setCurrentVideo({ ...currentVideo, status: 'processing' });
      setProcessingProgress({
         status: 'processing',
         current_frame: 0,
         total_frames: 100,
         message: 'Initializing...'
      });
    } catch (e) {
      console.error(e);
      toast.error('Failed to start');
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!currentVideo) return;
    
    const newUserMsg: ChatMessage = { role: 'user', content: text };
    setChatMessages(prev => [...prev, newUserMsg]);

    try {
      const res = await api.askQuestion(currentVideo.id, text);
      const newBotMsg: ChatMessage = { 
        role: 'assistant', 
        content: res.answer, 
        sources: res.sources 
      };
      setChatMessages(prev => [...prev, newBotMsg]);
    } catch (e) {
      console.error(e);
      toast.error('Failed to get answer');
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
    }
  };

  const handleVideoSelect = (video: Video) => {
    setCurrentVideo(video);
    setChatMessages([]); 
    setProcessingProgress(null);
    setViewMode('video');
  };

  const handleSeek = (seconds: number) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = seconds;
      videoPlayerRef.current.play();
    }
  };

  const handleSearchResultSelect = async (videoId: string, timestamp: number) => {
    // Find the video
    const video = videos.find(v => v.id === videoId);
    if (video) {
      setCurrentVideo(video);
      setChatMessages([]);
      setProcessingProgress(null);
      setViewMode('video');
      setPendingSeek(timestamp);
    } else {
      // Video might not be in current list, reload and try again
      await loadVideos();
      const updatedVideo = videos.find(v => v.id === videoId);
      if (updatedVideo) {
        setCurrentVideo(updatedVideo);
        setViewMode('video');
        setPendingSeek(timestamp);
      }
    }
  };

  const handleGoToSearch = () => {
    setViewMode('search');
  };

  return (
    <div className="flex h-screen bg-white font-sans text-zinc-900 selection:bg-zinc-900 selection:text-white">
      <Toaster position="bottom-right" theme="light" />
      
      <Sidebar 
        videos={videos}
        currentVideo={currentVideo}
        onSelectVideo={handleVideoSelect}
        onUpload={handleUpload}
        onRefresh={loadVideos}
        onDeleteVideo={handleDeleteVideo}
        onProcessVideo={async (videoId) => {
          const video = videos.find(v => v.id === videoId);
          if (video) {
            setCurrentVideo(video);
            setViewMode('video');
            try {
              await api.processVideo(videoId);
              setCurrentVideo({ ...video, status: 'processing' });
              setProcessingProgress({
                status: 'processing',
                current_frame: 0,
                total_frames: 100,
                message: 'Initializing...'
              });
            } catch (e) {
              console.error(e);
            }
          }
        }}
        onStopProcessing={async (videoId) => {
          try {
            await api.stopProcessing(videoId);
            toast.success('Processing stopped');
            setProcessingProgress(null);
            loadVideos();
          } catch (e) {
            console.error(e);
            // Even if API fails, reset local state
            setProcessingProgress(null);
            loadVideos();
          }
        }}
        isUploading={isUploading}
        onGoToSearch={handleGoToSearch}
        viewMode={viewMode}
      />
      
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-zinc-50/50">
        {viewMode === 'search' ? (
          <Dashboard 
            videos={videos}
            onSelectResult={handleSearchResultSelect}
            onSelectVideo={handleVideoSelect}
            onProcessVideo={async (videoId) => {
              const video = videos.find(v => v.id === videoId);
              if (video) {
                setCurrentVideo(video);
                setViewMode('video');
                try {
                  await api.processVideo(videoId);
                  setCurrentVideo({ ...video, status: 'processing' });
                  setProcessingProgress({
                    status: 'processing',
                    current_frame: 0,
                    total_frames: 100,
                    message: 'Initializing...'
                  });
                } catch (e) {
                  console.error(e);
                }
              }
            }}
          />
        ) : (
          <div className="flex-1 p-8 grid grid-cols-12 gap-8 min-h-0">
            <div className="col-span-12 lg:col-span-8 flex flex-col min-h-0 overflow-y-auto pr-2">
               <VideoPlayer 
                 video={currentVideo}
                 processingProgress={processingProgress}
                 onProcess={handleProcess}
                 playerRef={videoPlayerRef}
               />
            </div>
            
            <div className="col-span-12 lg:col-span-4 flex flex-col min-h-0 h-full">
              <Chat 
                messages={chatMessages}
                onSendMessage={handleSendMessage}
                onSeek={handleSeek}
                disabled={!currentVideo || currentVideo.status !== 'completed'}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

