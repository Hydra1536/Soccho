import { useEffect, useState } from 'react';
import { Search, X, Clock, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import axios from 'axios';
import api, { USER_ID_KEY } from '../../lib/api';
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
  total_given?: number;
  total_received?: number;
  total_transactions?: number;
};

type SearchHistoryItem = {
  query: string;
  ts: number;
};

type PendingRequestRow = {
  id: string;
  requester_id: string;
  addressee_id: string;
  counterpart_id: string;
  counterpart_username?: string;
  status: string;
};

type FriendListRow = {
  id: string;
  requester_id: string;
  addressee_id: string;
  counterpart_id: string;
  counterpart_username?: string;
  status: string;
};

type FriendListResponse = {
  next?: string | null;
  results?: FriendListRow[];
};

export default function FindFriends() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchErrorMessage, setSearchErrorMessage] = useState('');
  const [requestedUserIds, setRequestedUserIds] = useState<Record<string, boolean>>({});
  const [acceptedFriendships, setAcceptedFriendships] = useState<Record<string, string>>({});
  const [requestInFlight, setRequestInFlight] = useState<Record<string, boolean>>({});
  const [incomingRequests, setIncomingRequests] = useState<PendingRequestRow[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<PendingRequestRow[]>([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [pendingActionInFlight, setPendingActionInFlight] = useState<Record<string, boolean>>({});

  const fetchSearchResults = async (query: string) => {
    setIsSearching(true);
    setSearchErrorMessage('');
    try {
      const { data } = await api.get('/api/social/search/', { params: { q: query } });
      setSearchResults(data?.results || []);
    } catch (error) {
      setSearchResults([]);
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        setSearchErrorMessage('Session expired. Please sign in again.');
        return;
      }
      setSearchErrorMessage('Unable to search right now.');
    } finally {
      setIsSearching(false);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const { data } = await api.get('/api/social/search/history/');
      const raw = data?.history || data || [];
      const parsed = raw
        .map((item: string | SearchHistoryItem) => {
          if (typeof item !== 'string') {
            return item;
          }
          try {
            return JSON.parse(item) as SearchHistoryItem;
          } catch {
            return null;
          }
        })
        .filter((item: SearchHistoryItem | null): item is SearchHistoryItem => !!item?.query);
      setSearchHistory(parsed);
    } catch {
      setSearchHistory([]);
    }
  };

  const fetchPendingRequests = async () => {
    setPendingLoading(true);
    try {
      const { data } = await api.get('/api/social/requests/');
      const outgoing = Array.isArray(data?.outgoing) ? (data.outgoing as PendingRequestRow[]) : [];
      const incoming = Array.isArray(data?.incoming) ? (data.incoming as PendingRequestRow[]) : [];
      const outgoingMap = outgoing.reduce<Record<string, boolean>>((acc, row) => {
        const target = String(row.counterpart_id || '').trim();
        if (target) {
          acc[target] = true;
        }
        return acc;
      }, {});
      setRequestedUserIds(outgoingMap);
      setIncomingRequests(incoming);
      setOutgoingRequests(outgoing);
    } catch {
      setIncomingRequests([]);
      setOutgoingRequests([]);
    } finally {
      setPendingLoading(false);
    }
  };

  const fetchAcceptedFriends = async () => {
    const byUserId: Record<string, string> = {};
    let cursor: string | null = null;
    let safety = 0;
    const currentUserId = String(localStorage.getItem(USER_ID_KEY) || '').trim();

    try {
      while (safety < 50) {
        const params = cursor ? { cursor } : {};
        const { data } = await api.get<FriendListResponse>('/api/social/list/', { params });
        const rows = Array.isArray(data?.results) ? data.results : [];
        rows.forEach((row) => {
          const requesterId = String(row.requester_id || '').trim();
          const addresseeId = String(row.addressee_id || '').trim();
          const fallbackCounterpartId =
            requesterId && addresseeId
              ? (requesterId === currentUserId ? addresseeId : requesterId)
              : '';
          const counterpartId = String(row.counterpart_id || fallbackCounterpartId || '').trim();
          const friendshipId = String(row.id || '').trim();
          if (counterpartId && friendshipId) {
            byUserId[counterpartId] = friendshipId;
          }
        });

        const next = data?.next || null;
        if (!next) {
          break;
        }

        try {
          const parsed = next.startsWith('http') ? new URL(next) : new URL(next, window.location.origin);
          cursor = parsed.searchParams.get('cursor');
        } catch {
          cursor = null;
        }

        if (!cursor) {
          break;
        }
        safety += 1;
      }
      setAcceptedFriendships(byUserId);
    } catch {
      setAcceptedFriendships({});
    }
  };

  useEffect(() => {
    void fetchPendingRequests();
    void fetchAcceptedFriends();
  }, []);

  useEffect(() => {
    if (searchQuery.trim().length > 0) {
      void fetchSearchResults(searchQuery.trim());
      setShowResults(true);
    } else {
      setShowResults(false);
    }
  }, [searchQuery]);

  const handleSearch = (query: string) => {
    setSearchErrorMessage('');
    setSearchQuery(query);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowResults(false);
    setSearchErrorMessage('');
  };

  const normalizeScore = (person: SearchResult) => {
    const raw = person.loyaltyScore ?? person.loyalty_score ?? 0;
    const bounded = Math.max(0, Math.min(100, Number(raw) || 0));
    return bounded;
  };

  const totalVolume = (person: SearchResult) => {
    const given = Number(person.total_given || 0);
    const received = Number(person.total_received || 0);
    return Math.max(0, given) + Math.max(0, received);
  };

  const handleAddFriend = async (person: SearchResult) => {
    const targetId = String(person.user_id || person.id || '').trim();
    if (!targetId) {
      setSearchErrorMessage('Unable to send request for this user.');
      return;
    }

    const currentUserId = (localStorage.getItem(USER_ID_KEY) || '').trim();
    if (currentUserId && currentUserId === targetId) {
      setSearchErrorMessage('You cannot send a friend request to yourself.');
      return;
    }

    setRequestInFlight((prev) => ({ ...prev, [targetId]: true }));
    setSearchErrorMessage('');
    try {
      await api.post('/api/social/send-request/', { user_id: targetId });
      setRequestedUserIds((prev) => ({ ...prev, [targetId]: true }));
      void fetchPendingRequests();
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setRequestedUserIds((prev) => ({ ...prev, [targetId]: true }));
        void fetchPendingRequests();
      } else {
        setSearchErrorMessage(getErrorMessage(error));
      }
    } finally {
      setRequestInFlight((prev) => ({ ...prev, [targetId]: false }));
    }
  };

  const getErrorMessage = (error: unknown): string => {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
      if (error.response?.status === 401) {
        return 'Session expired. Please sign in again.';
      }
    }
    return 'Unable to send friend request right now.';
  };

  const handleWithdrawRequest = async (requestRow: PendingRequestRow) => {
    const addresseeId = String(requestRow.counterpart_id || requestRow.addressee_id || '').trim();
    const requestId = String(requestRow.id || '').trim();
    if (!addresseeId || !requestId) {
      return;
    }

    setPendingActionInFlight((prev) => ({ ...prev, [requestId]: true }));
    setSearchErrorMessage('');
    try {
      await api.post('/api/social/withdraw-request/', { user_id: addresseeId });
      setOutgoingRequests((prev) => prev.filter((row) => String(row.id) !== requestId));
      setRequestedUserIds((prev) => {
        const next = { ...prev };
        delete next[addresseeId];
        return next;
      });
    } catch (error) {
      setSearchErrorMessage(getErrorMessage(error));
    } finally {
      setPendingActionInFlight((prev) => ({ ...prev, [requestId]: false }));
    }
  };

  const handleIncomingAction = async (requestRow: PendingRequestRow, action: 'accept' | 'reject') => {
    const requesterId = String(requestRow.counterpart_id || requestRow.requester_id || '').trim();
    if (!requesterId) {
      return;
    }

    const requestId = String(requestRow.id || '').trim();
    if (!requestId) {
      return;
    }

    setPendingActionInFlight((prev) => ({ ...prev, [requestId]: true }));
    setSearchErrorMessage('');
    try {
      const endpoint = action === 'accept' ? '/api/social/accept/' : '/api/social/reject/';
      await api.post(endpoint, { user_id: requesterId });
      setIncomingRequests((prev) => prev.filter((row) => String(row.id) !== requestId));
      void fetchPendingRequests();
      void fetchAcceptedFriends();
    } catch (error) {
      setSearchErrorMessage(getErrorMessage(error));
    } finally {
      setPendingActionInFlight((prev) => ({ ...prev, [requestId]: false }));
    }
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
        <div>
          <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Outgoing Requests
          </h2>
          {pendingLoading && <p className="text-sm text-[#6B7280] mb-3">Loading requests...</p>}
          {!pendingLoading && outgoingRequests.length === 0 && <p className="text-sm text-[#6B7280] mb-3">No outgoing requests.</p>}
          <div className="space-y-3">
            {outgoingRequests.map((row, idx) => {
              const requestId = String(row.id || '');
              const isActing = !!pendingActionInFlight[requestId];
              return (
                <div key={requestId || idx} className="bg-white rounded-2xl p-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <Avatar name={row.counterpart_username || 'User'} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{row.counterpart_username || 'Unknown user'}</h3>
                      <p className="text-xs text-[#6B7280]">Friend request sent</p>
                    </div>
                    <button
                      onClick={() => void handleWithdrawRequest(row)}
                      disabled={isActing}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                        isActing ? 'bg-[#A5B4FC] text-white' : 'bg-[#EF4444] text-white hover:bg-[#DC2626]'
                      }`}
                    >
                      {isActing ? 'Cancelling...' : 'Cancel'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Incoming Requests
          </h2>
          {pendingLoading && <p className="text-sm text-[#6B7280] mb-3">Loading requests...</p>}
          {!pendingLoading && incomingRequests.length === 0 && <p className="text-sm text-[#6B7280] mb-3">No incoming requests.</p>}
          <div className="space-y-3">
            {incomingRequests.map((row, idx) => {
              const requestId = String(row.id || '');
              const isActing = !!pendingActionInFlight[requestId];
              return (
                <div key={requestId || idx} className="bg-white rounded-2xl p-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <Avatar name={row.counterpart_username || 'User'} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{row.counterpart_username || 'Unknown user'}</h3>
                      <p className="text-xs text-[#6B7280]">sent you a friend request</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => void handleIncomingAction(row, 'accept')}
                        disabled={isActing}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                          isActing ? 'bg-[#A5B4FC] text-white' : 'bg-[#10B981] text-white hover:bg-[#059669]'
                        }`}
                      >
                        Accept
                      </button>
                      <button
                        onClick={() => void handleIncomingAction(row, 'reject')}
                        disabled={isActing}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                          isActing ? 'bg-[#FCA5A5] text-white' : 'bg-[#EF4444] text-white hover:bg-[#DC2626]'
                        }`}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

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
            {isSearching && <p className="text-sm text-[#6B7280] mb-3">Searching...</p>}
            {searchErrorMessage && <p className="text-sm text-[#B45309] mb-3">{searchErrorMessage}</p>}
            <div className="space-y-3">
              {searchResults.map((person, idx) => {
                const targetId = String(person.user_id || person.id || '').trim();
                const friendshipId = targetId ? acceptedFriendships[targetId] : '';
                const isAlreadyFriend = !!friendshipId;
                const isRequested = targetId ? !!requestedUserIds[targetId] : false;
                const isLoading = targetId ? !!requestInFlight[targetId] : false;

                return (
                <div
                  key={person.user_id || person.id || idx}
                  className={`bg-white rounded-2xl p-4 shadow-sm ${isAlreadyFriend ? 'cursor-pointer hover:shadow-md transition-all' : ''}`}
                  onClick={() => {
                    if (!isAlreadyFriend) {
                      return;
                    }
                    navigate(`/friend/${friendshipId}`);
                  }}
                  role={isAlreadyFriend ? 'button' : undefined}
                  tabIndex={isAlreadyFriend ? 0 : undefined}
                  onKeyDown={(event) => {
                    if (!isAlreadyFriend) {
                      return;
                    }
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      navigate(`/friend/${friendshipId}`);
                    }
                  }}
                >
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
                        <p className="text-xs text-[#6B7280] mt-1">
                          Total Tx: {Number((person.total_transactions ?? person.totalTransactions) || 0).toLocaleString()} | Volume: TK {totalVolume(person).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        if (isAlreadyFriend) {
                          navigate(`/friend/${friendshipId}`);
                          return;
                        }
                        void handleAddFriend(person);
                      }}
                      disabled={isRequested || isLoading || !targetId}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                        isAlreadyFriend
                          ? 'bg-[#E5E7EB] text-[#374151]'
                          : isRequested
                          ? 'bg-[#E5E7EB] text-[#6B7280]'
                          : isLoading
                            ? 'bg-[#A5B4FC] text-white'
                            : 'bg-[#4F46E5] text-white hover:bg-[#3730A3]'
                      }`}
                    >
                      {isAlreadyFriend ? 'Profile' : isRequested ? 'Requested' : isLoading ? 'Sending...' : 'Add'}
                    </button>
                  </div>
                </div>
              )})}
            </div>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
