import { useState } from 'react';
import { Search, X, Clock, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Avatar } from '../components/Avatar';
import { Button } from '../components/Button';
import { BottomNav } from '../components/BottomNav';

const searchHistory = [
  'Rahim Khan',
  'Fatima Ahmed',
  'Karim Hossain'
];

const searchResults = [
  { id: 1, name: 'Salma Begum', mutualFriends: 12, loyaltyScore: 85 },
  { id: 2, name: 'Hasib Rahman', mutualFriends: 8, loyaltyScore: 72 },
  { id: 3, name: 'Nadia Islam', mutualFriends: 15, loyaltyScore: 90 }
];

const suggestedFriends = [
  { id: 4, name: 'Tahmid Chowdhury', mutualFriends: 20, loyaltyScore: 95 },
  { id: 5, name: 'Sabrina Akter', mutualFriends: 18, loyaltyScore: 88 },
  { id: 6, name: 'Fahim Hasan', mutualFriends: 10, loyaltyScore: 78 },
  { id: 7, name: 'Riya Sultana', mutualFriends: 14, loyaltyScore: 82 }
];

export default function FindFriends() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setShowResults(query.length > 0);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowResults(false);
  };

  const handleAddFriend = (id: number, name: string) => {
    console.log('Adding friend:', id, name);
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      {/* Header */}
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
          <button
            onClick={() => navigate('/home')}
            className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Find Friends
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Search Bar */}
        <div className="relative">
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B7280]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setTimeout(() => setIsFocused(false), 200)}
              placeholder="Search by name or phone..."
              className="w-full h-12 pl-12 pr-12 bg-white border border-[#E5E7EB] rounded-xl text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#111827]"
              >
                <X size={20} />
              </button>
            )}
          </div>

          {/* Search History Dropdown */}
          {isFocused && !showResults && searchHistory.length > 0 && (
            <div className="absolute top-full mt-2 w-full bg-white rounded-xl border border-[#E5E7EB] shadow-lg overflow-hidden z-20">
              {searchHistory.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleSearch(item)}
                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB] last:border-b-0"
                >
                  <Clock size={16} className="text-[#6B7280]" />
                  <span className="text-[#111827]">{item}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search Results */}
        {showResults && (
          <div>
            <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
              Results
            </h2>
            <div className="space-y-3">
              {searchResults.map((person) => (
                <div
                  key={person.id}
                  className="bg-white rounded-2xl p-4 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <Avatar name={person.name} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{person.name}</h3>
                      <p className="text-sm text-[#6B7280]">{person.mutualFriends} mutual friends</p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-[#E5E7EB] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#4F46E5] rounded-full transition-all"
                            style={{ width: `${person.loyaltyScore}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleAddFriend(person.id, person.name)}
                      className="px-4 py-2 bg-[#4F46E5] text-white rounded-full text-sm font-medium hover:bg-[#3730A3] transition-colors"
                    >
                      Add
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Friends */}
        {!showResults && (
          <div>
            <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
              Suggested Friends
            </h2>
            <p className="text-sm text-[#6B7280] mb-4">Based on loyalty score and mutual connections</p>
            <div className="space-y-3">
              {suggestedFriends.map((person) => (
                <div
                  key={person.id}
                  className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-3">
                    <Avatar name={person.name} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{person.name}</h3>
                      <p className="text-sm text-[#6B7280]">{person.mutualFriends} mutual friends</p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-[#E5E7EB] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-[#4F46E5] to-[#7C3AED] rounded-full transition-all"
                            style={{ width: `${person.loyaltyScore}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleAddFriend(person.id, person.name)}
                      className="px-4 py-2 bg-[#4F46E5] text-white rounded-full text-sm font-medium hover:bg-[#3730A3] transition-colors"
                    >
                      Add
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <button className="w-full mt-4 py-3 border-2 border-[#4F46E5] text-[#4F46E5] rounded-xl font-medium hover:bg-[#F3F4F6] transition-colors">
              Show More
            </button>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
