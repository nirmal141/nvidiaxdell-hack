import type { Video, UploadResponse, QuestionResponse, ProcessingProgress } from './types';

const API_BASE = '/api';

export const api = {
    async fetchVideos(): Promise<{ videos: Video[] }> {
        const res = await fetch(`${API_BASE}/videos`);
        if (!res.ok) throw new Error('Failed to fetch videos');
        return res.json();
    },

    async uploadVideo(file: File): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${API_BASE}/videos/upload`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) throw new Error('Failed to upload video');
        return res.json();
    },

    async processVideo(videoId: string): Promise<any> {
        const res = await fetch(`${API_BASE}/videos/${videoId}/process`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error('Failed to start processing');
        return res.json();
    },

    async getVideoStatus(videoId: string): Promise<ProcessingProgress> {
        const res = await fetch(`${API_BASE}/videos/${videoId}/status`);
        if (!res.ok) throw new Error('Failed to get status');
        return res.json();
    },

    async askQuestion(videoId: string, question: string): Promise<QuestionResponse> {
        const res = await fetch(`${API_BASE}/videos/${videoId}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: videoId, question }),
        });
        if (!res.ok) throw new Error('Failed to get answer');
        return res.json();
    },

    async deleteVideo(videoId: string): Promise<any> {
        const res = await fetch(`${API_BASE}/videos/${videoId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error('Failed to delete video');
        return res.json();
    },

    getVideoStreamUrl(videoId: string) {
        return `${API_BASE}/videos/${videoId}/stream`;
    },

    getThumbnailUrl(videoId: string) {
        return `${API_BASE}/videos/${videoId}/thumbnail`;
    }
};
