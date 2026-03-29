import { useQuery } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { adminFetch } from '../api/client';
import { AlertCircle } from 'lucide-react';

interface Trend {
  query: string;
  match_type: string;
  count: number;
  last_seen: string;
}

interface Inquiry {
  id: number;
  user_name: string;
  user_email: string;
  message: string;
  match_type: string;
  search_context: Record<string, unknown>;
  status: string;
  created_at: string;
}

const MATCH_TYPE_LABELS: Record<string, { label: string; colour: string }> = {
  strong_match: { label: 'Strong Match', colour: 'bg-green-100 text-green-800' },
  ambiguous: { label: 'Ambiguous', colour: 'bg-yellow-100 text-yellow-800' },
  not_covered: { label: 'Not Covered', colour: 'bg-red-100 text-red-800' },
  partially_related: { label: 'Partial', colour: 'bg-orange-100 text-orange-800' },
  not_related: { label: 'Not Related', colour: 'bg-gray-100 text-gray-600' },
};

export default function TrendsDashboard() {
  const { adminKey } = useOutletContext<{ adminKey: string }>();

  const { data: trends } = useQuery<Trend[]>({
    queryKey: ['admin', 'trends'],
    queryFn: () => adminFetch('/admin/inquiries/trends', adminKey),
    staleTime: 30 * 1000,
  });

  const { data: inquiries } = useQuery<Inquiry[]>({
    queryKey: ['admin', 'inquiries'],
    queryFn: () => adminFetch('/admin/inquiries', adminKey),
    staleTime: 30 * 1000,
  });

  const contentGaps = trends?.filter(t => t.match_type === 'not_covered') ?? [];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Inquiry Trends</h1>

      {contentGaps.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={18} className="text-red-600" />
            <h3 className="font-semibold text-red-800">Content Gaps Detected</h3>
          </div>
          <p className="text-sm text-red-700 mb-3">These topics are within MCCAA's remit but have no published article:</p>
          <div className="flex flex-wrap gap-2">
            {contentGaps.map(g => (
              <span key={g.query} className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
                {g.query} ({g.count}x)
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-700">Top Search Queries</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Query</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Match Type</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Count</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {trends?.map((t, i) => {
              const mt = MATCH_TYPE_LABELS[t.match_type] ?? { label: t.match_type, colour: 'bg-gray-100 text-gray-600' };
              return (
                <tr key={i} className="border-b border-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-900">{t.query}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${mt.colour}`}>{mt.label}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">{t.count}</td>
                  <td className="px-4 py-2 text-gray-400">{new Date(t.last_seen).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {(!trends || trends.length === 0) && (
          <div className="text-center py-8 text-gray-400">No inquiry data yet</div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-700">Recent Inquiries</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {inquiries?.slice(0, 20).map(inq => (
            <div key={inq.id} className="px-4 py-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900 text-sm">{inq.user_name || 'Anonymous'}</span>
                <span className="text-xs text-gray-400">{new Date(inq.created_at).toLocaleDateString()}</span>
              </div>
              <p className="text-sm text-gray-600">{inq.message}</p>
              {inq.match_type && (
                <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                  MATCH_TYPE_LABELS[inq.match_type]?.colour ?? 'bg-gray-100 text-gray-600'
                }`}>
                  {MATCH_TYPE_LABELS[inq.match_type]?.label ?? inq.match_type}
                </span>
              )}
            </div>
          ))}
          {(!inquiries || inquiries.length === 0) && (
            <div className="text-center py-8 text-gray-400">No inquiries yet</div>
          )}
        </div>
      </div>
    </div>
  );
}
