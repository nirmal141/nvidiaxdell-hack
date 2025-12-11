import { useState } from 'react';
import { Search, Clock, Play, Sparkles, Loader2 } from 'lucide-react';
import type { GlobalSearchResult, GlobalSearchResponse } from '../types';
import { api } from '../api';

interface GlobalSearchProps {
  onSelectResult: (videoId: string, timestamp: number) => void;
}

export function GlobalSearch({ onSelectResult }: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<GlobalSearchResponse | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
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
  };

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col h-full bg-zinc-50">
      {/* Search Header */}
      <div className="text-center py-16 px-8 bg-white border-b border-zinc-100">
        <h1 className="text-2xl font-semibold text-zinc-900 mb-1">Sentio</h1>
        <p className="text-zinc-500 text-sm mb-8">Search across all your video footage</p>
        
        {/* Search Bar */}
        <div className="max-w-xl mx-auto">
          <div className="flex items-center bg-white border border-zinc-200 rounded-lg shadow-sm focus-within:border-zinc-400 focus-within:shadow transition-all">
            <Search className="w-4 h-4 ml-4 text-zinc-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search for events, objects, actions..."
              className="flex-1 px-3 py-3 text-sm bg-transparent outline-none placeholder:text-zinc-400"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="m-1.5 px-4 py-1.5 bg-zinc-900 text-white rounded text-sm font-medium hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
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
        
        {/* Quick Suggestions */}
        {!results && (
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {['fire incidents', 'vehicle accidents', 'suspicious activity', 'violence'].map((s) => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                className="px-3 py-1.5 text-xs bg-zinc-100 hover:bg-zinc-200 text-zinc-600 rounded-full transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div className="flex-1 overflow-y-auto p-6">
          {/* AI Summary */}
          {results.answer && (
            <div className="max-w-3xl mx-auto mb-6 p-4 bg-white border border-zinc-200 rounded-lg">
              <div className="text-[10px] font-medium text-zinc-400 uppercase tracking-wider mb-1.5">AI Summary</div>
              <p className="text-sm text-zinc-700 leading-relaxed">{results.answer}</p>
            </div>
          )}

          {/* Results Grid */}
          <div className="max-w-5xl mx-auto">
            <div className="text-sm text-zinc-500 mb-4">
              {results.total_results} results for "{results.query}"
            </div>

            {results.total_results === 0 ? (
              <div className="text-center py-12 text-zinc-400 text-sm">
                No matching content found
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {results.results.map((result, index) => (
                  <ResultCard
                    key={`${result.video_id}-${result.timestamp}-${index}`}
                    result={result}
                    onClick={() => onSelectResult(result.video_id, result.timestamp)}
                    formatTimestamp={formatTimestamp}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface ResultCardProps {
  result: GlobalSearchResult;
  onClick: () => void;
  formatTimestamp: (seconds: number) => string;
}

function ResultCard({ result, onClick, formatTimestamp }: ResultCardProps) {
  return (
    <button
      onClick={onClick}
      className="group text-left bg-white border border-zinc-200 rounded-lg overflow-hidden hover:shadow-md hover:border-zinc-300 transition-all"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-zinc-100">
        {result.thumbnail_url ? (
          <img
            src={result.thumbnail_url}
            alt={result.video_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-300">
            <Play className="w-6 h-6" />
          </div>
        )}
        
        {/* Timestamp */}
        <div className="absolute bottom-1.5 left-1.5 flex items-center gap-1 px-1.5 py-0.5 bg-black/70 text-white text-[10px] font-mono rounded">
          <Clock className="w-2.5 h-2.5" />
          {formatTimestamp(result.timestamp)}
        </div>
        
        {/* Play Overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/20 transition-colors">
          <div className="w-8 h-8 flex items-center justify-center bg-white rounded-full opacity-0 group-hover:opacity-100 scale-75 group-hover:scale-100 transition-all shadow">
            <Play className="w-3 h-3 text-zinc-900 ml-0.5" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="p-2.5">
        <div className="text-xs font-medium text-zinc-800 truncate">{result.video_name}</div>
        <p className="text-[10px] text-zinc-500 line-clamp-2 mt-0.5">{result.description}</p>
        <div className="mt-1.5 flex items-center gap-1.5">
          <div className="flex-1 h-1 bg-zinc-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${Math.round(result.relevance_score * 100)}%` }}
            />
          </div>
          <span className="text-[9px] text-zinc-400">{Math.round(result.relevance_score * 100)}%</span>
        </div>
      </div>
    </button>
  );
}
