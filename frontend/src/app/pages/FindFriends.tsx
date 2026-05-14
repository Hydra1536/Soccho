import { useEffect, useState } from 'react';
import { Search, X, Clock, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import api from '../../lib/api';
import { Avatar } from '../components/Avatar';
import { BottomNav } from '../components/BottomNav';

type SearchResult = {
  id?: string;
  user_id?: string;
  username?: string;
  name?: string;
  mutualFriends?: number;
  loyaltyScore?: number;
  loyalty_score?: number;
};

type SearchHistoryItem = {
  query: string;
  ts: number;
};

export default function FindFriends() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  const fetchSearchResults = async (query: string) => {
    const { data } = await api.get('/api/social/search/', { params: { q: query } });
    setSearchResults(data?.results || []);
  };

  const fetchSearchHistory = async () => {
    const { data } = await api.get('/api/social/search/history/');
    const raw = data?.history || data || [];
    const parsed = raw
      .map((item: string | SearchHistoryItem) => (typeof item === 'string' ? JSON.parse(item) : item))
      .filter((item: SearchHistoryItem) => item?.query);
    setSearchHistory(parsed);
  };

  useEffect(() => {
    if (searchQuery.trim().length > 0) {
      void fetchSearchResults(searchQuery.trim());
      setShowResults(true);
    } else {
      setShowResults(false);
    }
  }, [searchQuery]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowResults(false);
  };

  const normalizeScore = (person: SearchResult) => {
    const raw = person.loyaltyScore ?? person.loyalty_score ?? 0;
    const bounded = Math.max(0, Math.min(100, Number(raw) || 0));
    return bounded;
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
          <button onClick={() => navigate('/home')} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Find Friends
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        <div className="relative">
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B7280]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => {
                setIsFocused(true);
                void fetchSearchHistory();
              }}
              onBlur={() => setTimeout(() => setIsFocused(false), 200)}
              placeholder="Search by name or phone..."
              className="w-full h-12 pl-12 pr-12 bg-white border border-[#E5E7EB] rounded-xl text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all"
            />
            {searchQuery && (
              <button onClick={clearSearch} className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#111827]">
                <X size={20} />
              </button>
            )}
          </div>

          {isFocused && !showResults && searchHistory.length > 0 && (
            <div className="absolute top-full mt-2 w-full bg-white rounded-xl border border-[#E5E7EB] shadow-lg overflow-hidden z-20">
              {searchHistory.map((item, index) => (
                <button key={index} onClick={() => handleSearch(item.query)} className="w-full px-4 py-3 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB] last:border-b-0">
                  <Clock size={16} className="text-[#6B7280]" />
                  <span className="text-[#111827]">{item.query}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {showResults && (
          <div>
            <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
              Results
            </h2>
            <div className="space-y-3">
              {searchResults.map((person, idx) => (
                <div key={person.user_id || person.id || idx} className="bg-white rounded-2xl p-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <Avatar name={person.username || person.name || `Friend ${idx + 1}`} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{person.username || person.name || `Friend ${idx + 1}`}</h3>
                      <div className="mt-2">
                        <div className="h-2 rounded-full bg-[#E5E7EB] overflow-hidden">
                          <div
                            className="h-full bg-[#4F46E5] rounded-full transition-all"
                            style={{ width: `${normalizeScore(person)}%` }}
                          />
                        </div>
                        <p className="text-xs text-[#6B7280] mt-1">Loyalty Score</p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-[#4F46E5] text-white rounded-full text-sm font-medium hover:bg-[#3730A3] transition-colors">
                      Add
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
