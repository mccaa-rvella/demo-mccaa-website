import { useState, useCallback } from 'react';
import { apiFetch } from '../api/client';

interface SearchResult {
  match_type: 'strong_match' | 'ambiguous' | 'not_covered' | 'partially_related' | 'not_related';
  article_slug: string | null;
  message: string | null;
  follow_up_question: string | null;
  show_contact_form: boolean;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function useSearch() {
  const [conversationId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const search = useCallback(async (query: string) => {
    setIsSearching(true);
    setMessages(prev => [...prev, { role: 'user', content: query }]);

    try {
      const res = await apiFetch<SearchResult>('/search', {
        method: 'POST',
        body: JSON.stringify({ query, conversation_id: conversationId }),
      });
      setResult(res);

      if (res.follow_up_question) {
        setMessages(prev => [...prev, { role: 'assistant', content: res.follow_up_question! }]);
      } else if (res.message) {
        setMessages(prev => [...prev, { role: 'assistant', content: res.message! }]);
      }

      return res;
    } finally {
      setIsSearching(false);
    }
  }, [conversationId]);

  const reset = useCallback(() => {
    setMessages([]);
    setResult(null);
  }, []);

  return { search, messages, result, isSearching, reset, conversationId };
}
