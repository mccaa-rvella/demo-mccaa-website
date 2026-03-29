import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Send } from 'lucide-react';
import { useSearch } from '../hooks/useSearch';
import ContactForm from '../components/ui/ContactForm';

export default function SearchBar() {
  const [input, setInput] = useState('');
  const { search, messages, result, isSearching, reset, conversationId } = useSearch();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isSearching) return;
    const query = input.trim();
    setInput('');
    const res = await search(query);
    if (res?.match_type === 'strong_match' && res.article_slug) {
      navigate(`/kb/${res.article_slug}`);
    }
  }

  const hasConversation = messages.length > 0;
  const showContactForm = result?.show_contact_form ?? false;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text" value={input} onChange={e => setInput(e.target.value)}
          placeholder="What do you need help with?"
          className="w-full bg-white/90 backdrop-blur rounded-full px-6 py-4 pr-14 text-gray-800 placeholder-gray-400 shadow-lg border border-white/50 focus:outline-none focus:ring-2 focus:ring-white/50 text-base"
        />
        <button type="submit" disabled={isSearching || !input.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 bg-white/30 hover:bg-white/50 p-2.5 rounded-full transition-colors disabled:opacity-30">
          {isSearching ? (
            <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin" />
          ) : (
            <Search size={18} className="text-white" />
          )}
        </button>
      </form>

      {hasConversation && (
        <div className="mt-4 bg-white/10 backdrop-blur rounded-2xl p-4 space-y-3 border border-white/20">
          {messages.map((msg, i) => (
            <div key={i} className={`text-sm ${msg.role === 'user' ? 'text-white/80' : 'text-white font-medium'}`}>
              <span className="text-white/50 text-xs">{msg.role === 'user' ? 'You' : 'MCCAA'}:</span>{' '}
              {msg.content}
            </div>
          ))}
          {result?.match_type === 'ambiguous' && (
            <form onSubmit={handleSubmit} className="flex gap-2 mt-2">
              <input type="text" value={input} onChange={e => setInput(e.target.value)}
                placeholder="Type your reply..."
                className="flex-1 bg-white/20 rounded-full px-4 py-2 text-sm text-white placeholder-white/40 border border-white/20 focus:outline-none" />
              <button type="submit" disabled={isSearching} className="bg-white/20 hover:bg-white/30 p-2 rounded-full transition-colors">
                <Send size={14} className="text-white" />
              </button>
            </form>
          )}
          {showContactForm && (
            <div className="mt-3">
              <ContactForm
                searchContext={{ query: messages.filter(m => m.role === 'user').map(m => m.content).join(' → '), conversation_id: conversationId }}
                matchType={result?.match_type}
              />
            </div>
          )}
          <button onClick={reset} className="text-xs text-white/40 hover:text-white/60 transition-colors">Clear search</button>
        </div>
      )}

      <p className="text-center text-white/50 text-xs mt-3">Try: "toy safety", "CE marking", "consumer rights"</p>
    </div>
  );
}
