import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { adminFetch } from '../api/client';
import ArticleDetail from './ArticleDetail';

interface Article {
  id: number;
  title: string;
  slug: string;
  sector: string;
  audience: string;
  status: string;
  updated_at: string;
  html_content: string;
  tag_map: Record<string, unknown>;
  skills_used: string[];
  source_knowledge_unit_ids: number[];
}

const STATUS_COLOURS: Record<string, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  published: 'bg-green-100 text-green-800',
  update_pending: 'bg-blue-100 text-blue-800',
  rejected: 'bg-red-100 text-red-800',
  archived: 'bg-gray-100 text-gray-500',
};

export default function ArticleList() {
  const { adminKey } = useOutletContext<{ adminKey: string }>();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [audienceFilter, setAudienceFilter] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: articles, isLoading } = useQuery<Article[]>({
    queryKey: ['admin', 'articles', statusFilter, audienceFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (audienceFilter) params.set('audience', audienceFilter);
      const qs = params.toString();
      return adminFetch(`/admin/articles${qs ? `?${qs}` : ''}`, adminKey);
    },
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => adminFetch(`/admin/articles/${id}/approve`, adminKey, {
      method: 'POST',
      body: JSON.stringify({ approved_by: 'admin@mccaa.org.mt' }),
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'articles'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => adminFetch(`/admin/articles/${id}/reject`, adminKey, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'articles'] }),
  });

  const selectedArticle = articles?.find(a => a.id === selectedId);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Articles</h1>
        <div className="flex gap-3">
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="update_pending">Update Pending</option>
            <option value="rejected">Rejected</option>
          </select>
          <select value={audienceFilter} onChange={e => setAudienceFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="">All audiences</option>
            <option value="business">Business</option>
            <option value="consumer">Consumer</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading articles...</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Title</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Sector</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Audience</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Updated</th>
              </tr>
            </thead>
            <tbody>
              {articles?.map(article => (
                <tr key={article.id}
                  onClick={() => setSelectedId(selectedId === article.id ? null : article.id)}
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${
                    selectedId === article.id ? 'bg-[#2da0a4]/5' : 'hover:bg-gray-50'
                  }`}>
                  <td className="px-4 py-3 font-medium text-gray-900">{article.title}</td>
                  <td className="px-4 py-3 text-gray-600">{article.sector}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{article.audience}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOURS[article.status] ?? ''}`}>
                      {article.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{new Date(article.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {selectedArticle && (
            <ArticleDetail article={selectedArticle}
              onApprove={() => approveMutation.mutate(selectedArticle.id)}
              onReject={() => rejectMutation.mutate(selectedArticle.id)}
              isApproving={approveMutation.isPending} isRejecting={rejectMutation.isPending} />
          )}
        </div>
      )}
    </div>
  );
}
