import { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { VideoPlayer } from './components/VideoPlayer';
import { Chat } from './components/Chat';
import type { Video, ChatMessage, ProcessingProgress } from './types';
import { api } from './api';
import { Toaster, toast } from 'sonner';

function App() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
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

    if (currentVideo?.id && (currentVideo.status === 'processing' || processingProgress?.status === 'processing')) {
       const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
       const host = window.location.host; 
       const wsUrl = `${protocol}//${host}/ws/progress/${currentVideo.id}`;
       
       ws = new WebSocket(wsUrl);

       ws.onmessage = (event) => {
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
       };

       ws.onerror = () => {
         // Silent fail on WS error
       };
    }

    return () => {
      if (ws) ws.close();
    };
  }, [currentVideo?.id, currentVideo?.status, processingProgress?.status]);


  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const res = await api.uploadVideo(file);
      if (res.success) {
        toast.success('Uploaded successfully');
        await loadVideos();
        setCurrentVideo(res.video); 
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
  };

  const handleSeek = (seconds: number) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = seconds;
      videoPlayerRef.current.play();
    }
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
        isUploading={isUploading}
      />
      
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-zinc-50/50">
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
      </main>
    </div>
  );
}

export default App;
