import { useState } from 'react';
import { apiFetch } from '../../api/client';

interface ContactFormProps {
  searchContext?: Record<string, unknown>;
  matchType?: string;
}

export default function ContactForm({ searchContext, matchType }: ContactFormProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiFetch('/contact', {
        method: 'POST',
        body: JSON.stringify({
          user_name: name,
          user_email: email,
          message,
          search_context: searchContext ?? {},
          match_type: matchType ?? 'general',
        }),
      });
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 text-sm">
        Thank you. We'll get back to you shortly.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="text-sm font-semibold text-gray-700">Contact the MCCAA</div>
      <input
        type="text" placeholder="Your name" value={name} onChange={e => setName(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <input
        type="email" placeholder="Your email" value={email} onChange={e => setEmail(e.target.value)}
        required
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <textarea
        placeholder="How can we help?" value={message} onChange={e => setMessage(e.target.value)}
        rows={3}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <button
        type="submit" disabled={submitting || !email}
        className="bg-[#2da0a4] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#258487] disabled:opacity-50 transition-colors"
      >
        {submitting ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
