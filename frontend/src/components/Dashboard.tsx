import { useState } from 'react';
import { Search, Clock, Play, Sparkles, Loader2, Database, ArrowUpDown, Eye, Zap, CheckCircle, AlertCircle, Clock3, Video } from 'lucide-react';
import type { GlobalSearchResult, GlobalSearchResponse, Video as VideoType } from '../types';
import { api } from '../api';

interface DashboardProps {
  videos: VideoType[];
  onSelectResult: (videoId: string, timestamp: number) => void;
  onSelectVideo: (video: VideoType) => void;
  onProcessVideo?: (videoId: string) => void;
}

export function Dashboard({ videos, onSelectResult, onSelectVideo, onProcessVideo }: DashboardProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<GlobalSearchResponse | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'duration' | 'status'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSearch = async () => {
    if (!query.trim()) {
      setResults(null);
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await api.globalSearch(query.trim());
      setResults(response);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
    if (e.key === 'Escape') {
      setQuery('');
      setResults(null);
    }
  };

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sortedVideos = [...videos].sort((a, b) => {
    let comparison = 0;
    if (sortBy === 'name') comparison = a.name.localeCompare(b.name);
    if (sortBy === 'duration') comparison = (a.duration || 0) - (b.duration || 0);
    if (sortBy === 'status') comparison = (a.status || '').localeCompare(b.status || '');
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const toggleSort = (field: 'name' | 'duration' | 'status') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3" />
            Ready
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processing
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-50 text-red-700 border border-red-200">
            <AlertCircle className="w-3 h-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-100 text-zinc-600 border border-zinc-200">
            <Clock3 className="w-3 h-3" />
            Pending
          </span>
        );
    }
  };

  const completedCount = videos.filter(v => v.status === 'completed').length;
  const processingCount = videos.filter(v => v.status === 'processing').length;
  const pendingCount = videos.filter(v => !v.status || v.status === 'pending').length;

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-zinc-200 bg-zinc-50/50">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-semibold text-zinc-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-zinc-400" />
                Video Intelligence Database
              </h1>
              <p className="text-sm text-zinc-500 mt-0.5">
                {videos.length} videos • {completedCount} analyzed • Search across all footage
              </p>
            </div>
            
            {/* Stats Pills */}
            <div className="flex items-center gap-2">
              <div className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg">
                <span className="text-xs font-medium text-emerald-700">{completedCount} Ready</span>
              </div>
              {processingCount > 0 && (
                <div className="px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
                  <span className="text-xs font-medium text-blue-700">{processingCount} Processing</span>
                </div>
              )}
              {pendingCount > 0 && (
                <div className="px-3 py-1.5 bg-zinc-100 border border-zinc-200 rounded-lg">
                  <span className="text-xs font-medium text-zinc-600">{pendingCount} Pending</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="flex items-center gap-3">
            <div className="flex-1 flex items-center bg-white border border-zinc-200 rounded-lg shadow-sm focus-within:border-zinc-400 focus-within:ring-2 focus-within:ring-zinc-100 transition-all">
              <Search className="w-4 h-4 ml-4 text-zinc-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search across all videos... (e.g., 'suspicious activity', 'vehicle accident', 'person running')"
                className="flex-1 px-3 py-2.5 text-sm bg-transparent outline-none placeholder:text-zinc-400"
              />
              {query && (
                <button
                  onClick={() => { setQuery(''); setResults(null); }}
                  className="px-2 text-zinc-400 hover:text-zinc-600"
                >
                  ✕
                </button>
              )}
              <button
                onClick={handleSearch}
                disabled={isSearching || !query.trim()}
                className="m-1 px-4 py-1.5 bg-zinc-900 text-white rounded-md text-sm font-medium hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
              >
                {isSearching ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>Search</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {results ? (
          /* Search Results View */
          <div className="p-8">
            {/* AI Summary */}
            {results.answer && (
              <div className="mb-6 p-4 bg-gradient-to-r from-zinc-50 to-zinc-100/50 border border-zinc-200 rounded-xl">
                <div className="flex items-center gap-2 text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
                  <Sparkles className="w-3.5 h-3.5" />
                  AI Analysis
                </div>
                <p className="text-sm text-zinc-700 leading-relaxed">{results.answer}</p>
              </div>
            )}

            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-zinc-900">
                {results.total_results} results for "{results.query}"
              </h2>
              <button
                onClick={() => { setQuery(''); setResults(null); }}
                className="text-xs text-zinc-500 hover:text-zinc-700 underline"
              >
                Clear search
              </button>
            </div>

            {results.total_results === 0 ? (
              <div className="text-center py-16">
                <Search className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                <p className="text-zinc-500">No matching content found</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {results.results.map((result, index) => (
                  <SearchResultCard
                    key={`${result.video_id}-${result.timestamp}-${index}`}
                    result={result}
                    onClick={() => onSelectResult(result.video_id, result.timestamp)}
                    formatTimestamp={formatTimestamp}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Database Table View */
          <div className="p-8">
            <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-zinc-50 border-b border-zinc-200 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                <div className="col-span-5 flex items-center gap-1 cursor-pointer hover:text-zinc-700" onClick={() => toggleSort('name')}>
                  <Video className="w-3.5 h-3.5" />
                  Video Name
                  <ArrowUpDown className="w-3 h-3" />
                </div>
                <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-zinc-700" onClick={() => toggleSort('duration')}>
                  <Clock className="w-3.5 h-3.5" />
                  Duration
                  <ArrowUpDown className="w-3 h-3" />
                </div>
                <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-zinc-700" onClick={() => toggleSort('status')}>
                  Status
                  <ArrowUpDown className="w-3 h-3" />
                </div>
                <div className="col-span-3 text-right">Actions</div>
              </div>

              {/* Table Body */}
              {videos.length === 0 ? (
                <div className="text-center py-16">
                  <Video className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                  <p className="text-zinc-500">No videos in database</p>
                  <p className="text-xs text-zinc-400 mt-1">Upload your first video to get started</p>
                </div>
              ) : (
                <div className="divide-y divide-zinc-100">
                  {sortedVideos.map((video) => (
                    <div
                      key={video.id}
                      className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-zinc-50/50 transition-colors group"
                    >
                      {/* Video Name */}
                      <div className="col-span-5 flex items-center gap-3">
                        <div className="w-16 h-10 bg-zinc-100 rounded overflow-hidden flex-shrink-0">
                          {video.thumbnail_url ? (
                            <img src={video.thumbnail_url} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-zinc-400">
                              <Play className="w-4 h-4" />
                            </div>
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-zinc-900 truncate">{video.name}</p>
                          <p className="text-[10px] text-zinc-400 font-mono truncate">{video.id}</p>
                        </div>
                      </div>

                      {/* Duration */}
                      <div className="col-span-2 flex items-center">
                        <span className="text-sm text-zinc-600 font-mono">{formatDuration(video.duration)}</span>
                      </div>

                      {/* Status */}
                      <div className="col-span-2 flex items-center">
                        {getStatusBadge(video.status)}
                      </div>

                      {/* Actions */}
                      <div className="col-span-3 flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {video.status === 'completed' ? (
                          <button
                            onClick={() => onSelectVideo(video)}
                            className="px-3 py-1.5 text-xs font-medium text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded-md transition-colors flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            View
                          </button>
                        ) : video.status !== 'processing' && onProcessVideo ? (
                          <button
                            onClick={() => onProcessVideo(video.id)}
                            className="px-3 py-1.5 text-xs font-medium text-white bg-zinc-900 hover:bg-zinc-800 rounded-md transition-colors flex items-center gap-1"
                          >
                            <Zap className="w-3 h-3" />
                            Analyze
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface SearchResultCardProps {
  result: GlobalSearchResult;
  onClick: () => void;
  formatTimestamp: (seconds: number) => string;
}

function SearchResultCard({ result, onClick, formatTimestamp }: SearchResultCardProps) {
  return (
    <button
      onClick={onClick}
      className="group text-left bg-white border border-zinc-200 rounded-lg overflow-hidden hover:shadow-lg hover:border-zinc-300 transition-all hover:-translate-y-0.5"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-zinc-100">
        {result.thumbnail_url ? (
          <img src={result.thumbnail_url} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-300">
            <Play className="w-6 h-6" />
          </div>
        )}
        
        {/* Timestamp Badge */}
        <div className="absolute bottom-1.5 left-1.5 flex items-center gap-1 px-1.5 py-0.5 bg-black/80 text-white text-[10px] font-mono rounded">
          <Clock className="w-2.5 h-2.5" />
          {formatTimestamp(result.timestamp)}
        </div>
        
        {/* Play Overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-colors">
          <div className="w-10 h-10 flex items-center justify-center bg-white rounded-full opacity-0 group-hover:opacity-100 scale-75 group-hover:scale-100 transition-all shadow-lg">
            <Play className="w-4 h-4 text-zinc-900 ml-0.5" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <div className="text-xs font-medium text-zinc-800 truncate">{result.video_name}</div>
        <p className="text-[10px] text-zinc-500 line-clamp-2 mt-1 leading-relaxed">{result.description}</p>
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1 bg-zinc-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${Math.round(result.relevance_score * 100)}%` }}
            />
          </div>
          <span className="text-[9px] font-medium text-zinc-400">{Math.round(result.relevance_score * 100)}%</span>
        </div>
      </div>
    </button>
  );
}
