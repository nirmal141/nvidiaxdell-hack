import { useEffect, useRef } from 'react';
import type { SegmentResponse } from '../types';

interface SegmentationOverlayProps {
  segment: SegmentResponse | null;
  videoWidth: number;
  videoHeight: number;
}

export function SegmentationOverlay({ segment, videoWidth, videoHeight }: SegmentationOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !segment || !segment.polygon.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw polygon mask
    ctx.beginPath();
    
    const points = segment.polygon;
    if (points.length < 3) return;
    
    // Move to first point
    const startX = points[0][0] * videoWidth;
    const startY = points[0][1] * videoHeight;
    ctx.moveTo(startX, startY);
    
    // Draw lines to remaining points
    for (let i = 1; i < points.length; i++) {
      const x = points[i][0] * videoWidth;
      const y = points[i][1] * videoHeight;
      ctx.lineTo(x, y);
    }
    
    ctx.closePath();
    
    // Fill with semi-transparent color
    ctx.fillStyle = 'rgba(0, 200, 255, 0.3)';
    ctx.fill();
    
    // Draw outline
    ctx.strokeStyle = '#00c8ff';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // Add glow effect
    ctx.shadowColor = '#00c8ff';
    ctx.shadowBlur = 10;
    ctx.stroke();

  }, [segment, videoWidth, videoHeight]);

  if (!segment) return null;

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
