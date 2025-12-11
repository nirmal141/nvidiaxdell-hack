import { useEffect, useRef } from 'react';
import type { DetectionResponse, DetectedObject } from '../types';

interface DetectionOverlayProps {
  detections: DetectionResponse | null;
  videoWidth: number;
  videoHeight: number;
}

// Color map for different object classes
const CLASS_COLORS: { [key: string]: string } = {
  person: '#ef4444',  // Red
  car: '#3b82f6',     // Blue
  truck: '#3b82f6',
  bus: '#3b82f6',
  motorcycle: '#8b5cf6', // Purple
  bicycle: '#8b5cf6',
  knife: '#dc2626',   // Dark red (weapon)
  backpack: '#22c55e', // Green
  handbag: '#22c55e',
  suitcase: '#22c55e',
  '🔥 FIRE': '#ff6600', // Orange for fire
  default: '#fbbf24'  // Yellow
};

function getColor(className: string): string {
  return CLASS_COLORS[className] || CLASS_COLORS.default;
}

export function DetectionOverlay({ detections, videoWidth, videoHeight }: DetectionOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !detections) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate scale factors
    const scaleX = videoWidth / detections.frame_width;
    const scaleY = videoHeight / detections.frame_height;

    // Draw each detection
    detections.detections.forEach((det: DetectedObject) => {
      const color = getColor(det.class_name);
      
      // Scale bounding box to video display size
      const x1 = det.bbox_pixels[0] * scaleX;
      const y1 = det.bbox_pixels[1] * scaleY;
      const x2 = det.bbox_pixels[2] * scaleX;
      const y2 = det.bbox_pixels[3] * scaleY;
      const width = x2 - x1;
      const height = y2 - y1;

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x1, y1, width, height);

      // Draw label background
      const label = `${det.class_name} ${Math.round(det.confidence * 100)}%`;
      ctx.font = 'bold 12px Inter, system-ui, sans-serif';
      const textWidth = ctx.measureText(label).width;
      const labelHeight = 18;
      
      ctx.fillStyle = color;
      ctx.fillRect(x1, y1 - labelHeight, textWidth + 8, labelHeight);

      // Draw label text
      ctx.fillStyle = 'white';
      ctx.fillText(label, x1 + 4, y1 - 5);
    });
  }, [detections, videoWidth, videoHeight]);

  if (!detections) return null;

  return (
    <canvas
      ref={canvasRef}
      width={videoWidth}
      height={videoHeight}
      className="absolute inset-0 pointer-events-none"
      style={{ width: videoWidth, height: videoHeight }}
    />
  );
}

interface DetectionStatsProps {
  detections: DetectionResponse | null;
  isLoading: boolean;
}

export function DetectionStats({ detections, isLoading }: DetectionStatsProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <div className="w-3 h-3 border-2 border-zinc-300 border-t-zinc-600 rounded-full animate-spin" />
        Detecting objects...
      </div>
    );
  }

  if (!detections) return null;

  return (
    <div className="flex items-center gap-4 text-xs">
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span className="text-zinc-600">
          <strong className="text-zinc-900">{detections.person_count}</strong> people
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-blue-500" />
        <span className="text-zinc-600">
          <strong className="text-zinc-900">{detections.vehicle_count}</strong> vehicles
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-yellow-500" />
        <span className="text-zinc-600">
          <strong className="text-zinc-900">{detections.detections.length}</strong> total
        </span>
      </div>
      <span className="text-zinc-400">
        {detections.inference_time_ms.toFixed(0)}ms
      </span>
    </div>
  );
}
