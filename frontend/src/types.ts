export interface Video {
    id: string;
    name: string;
    duration: number; // seconds
    status: 'pending' | 'processing' | 'completed' | 'failed';
    thumbnail_url?: string;
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

export interface GlobalSearchResult {
    video_id: string;
    video_name: string;
    timestamp: number;
    description: string;
    relevance_score: number;
    thumbnail_url: string | null;
}

export interface GlobalSearchResponse {
    query: string;
    results: GlobalSearchResult[];
    total_results: number;
    answer: string | null;
}

export interface DetectedObject {
    class_id: number;
    class_name: string;
    confidence: number;
    bbox: number[];  // [x1, y1, x2, y2] normalized 0-1
    bbox_pixels: number[];  // [x1, y1, x2, y2] in pixels
}

export interface DetectionResponse {
    video_id: string;
    timestamp: number;
    detections: DetectedObject[];
    frame_width: number;
    frame_height: number;
    inference_time_ms: number;
    person_count: number;
    vehicle_count: number;
}

export interface SegmentResponse {
    video_id: string;
    timestamp: number;
    polygon: number[][];  // [[x, y], [x, y], ...] normalized 0-1
    area: number;
    confidence: number;
}

