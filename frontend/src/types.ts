export interface Video {
    id: string;
    name: string;
    duration: number; // seconds
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at?: string;
}

export interface ChatSource {
    timestamp: number;
    description: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
}

export interface ProcessingProgress {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    current_frame: number;
    total_frames: number;
    message: string;
}

export interface UploadResponse {
    success: boolean;
    video: Video;
    error?: string;
}

export interface QuestionResponse {
    answer: string;
    sources: ChatSource[];
}
