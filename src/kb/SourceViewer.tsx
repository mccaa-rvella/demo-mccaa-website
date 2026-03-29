import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { apiFetch } from '../api/client';
import Sidebar from './Sidebar';

interface Article {
  id: number;
  title: string;
  slug: string;
  sector: string;
  scope: string;
  audience: string;
  html_content: string;
  tag_map: Record<string, { topics?: string[]; actors?: string[] }>;
  cross_cutting_summaries: Array<{ topic: string; scope: string; summary: string; article_slug: string }>;
  status: string;
  updated_at: string;
}

export default function SourceViewer() {
  const { slug } = useParams<{ slug: string }>();
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const { data: article, isLoading, error } = useQuery<Article>({
    queryKey: ['article', slug],
    queryFn: async () => {
      try {
        return await apiFetch<Article>(`/articles/${slug}`);
      } catch {
        const parts = slug?.split('-') ?? [];
        const audience = parts[parts.length - 1];
        const sectorSlug = audience === 'business' || audience === 'consumer'
          ? parts.slice(0, -1).join('-')
          : slug;
        const aud = audience === 'consumer' ? 'consumer' : 'business';
        return await apiFetch<Article>(`/articles/by-sector/${sectorSlug}?audience=${aud}`);
      }
    },
    enabled: !!slug,
  });

  useEffect(() => {
    if (article) {
      apiFetch('/track/visit', {
        method: 'POST',
        body: JSON.stringify({ sector: article.sector }),
      }).catch(() => {});
    }
  }, [article]);

  const { topics, actors } = useMemo(() => {
    if (!article?.tag_map) return { topics: [], actors: [] };
    const topicSet = new Set<string>();
    const actorSet = new Set<string>();
    for (const section of Object.values(article.tag_map)) {
      section.topics?.forEach(t => topicSet.add(t));
      section.actors?.forEach(a => actorSet.add(a));
    }
    return { topics: Array.from(topicSet), actors: Array.from(actorSet) };
  }, [article]);

  function handleTagClick(tag: string) {
    setActiveTag(prev => prev === tag ? null : tag);
    const sections = document.querySelectorAll('[data-topics], [data-actors]');
    for (const section of sections) {
      const sectionTopics = section.getAttribute('data-topics')?.split(',') ?? [];
      const sectionActors = section.getAttribute('data-actors')?.split(',') ?? [];
      if (sectionTopics.includes(tag) || sectionActors.includes(tag)) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        break;
      }
    }
  }

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center pt-24"><div className="animate-pulse text-[#2da0a4]">Loading article...</div></div>;
  }

  if (error || !article) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center pt-24 gap-4">
        <p className="text-gray-500">Article not found</p>
        <Link to="/kb" className="text-[#2da0a4] hover:underline">← Back to Knowledge Base</Link>
      </div>
    );
  }

  return (
    <div className="pt-24 max-w-6xl mx-auto px-4">
      <div className="mb-6">
        <Link to="/kb" className="text-sm text-[#2da0a4] hover:underline flex items-center gap-1 mb-3">
          <ArrowLeft size={14} /> Back to Knowledge Base
        </Link>
        <div className="flex items-center gap-3 mb-2">
          <span className="bg-[#2da0a4] text-white text-xs font-bold px-3 py-1 rounded-full">{article.sector}</span>
          {article.audience === 'consumer' && (
            <span className="bg-[#7a4a5f] text-white text-xs font-bold px-3 py-1 rounded-full">Consumer</span>
          )}
          <span className="text-xs text-gray-400">Updated {new Date(article.updated_at).toLocaleDateString()}</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{article.title}</h1>
        {article.status === 'update_pending' && (
          <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 text-sm text-yellow-800">
            This article is being updated with new information.
          </div>
        )}
      </div>

      <div className="flex gap-8 pb-16">
        <Sidebar topics={topics} actors={actors} crossCuttingSummaries={article.cross_cutting_summaries ?? []}
          activeTag={activeTag} audience={article.audience} onTagClick={handleTagClick} />

        <main className="flex-1 min-w-0">
          <div className="prose prose-gray max-w-none article-content"
            dangerouslySetInnerHTML={{ __html: article.html_content }} />

          {article.cross_cutting_summaries?.map((summary, i) => (
            <div key={i} className={`border-l-4 rounded-r-lg p-4 my-4 ${
              summary.scope === 'universal' ? 'border-l-[#b8e38d] bg-[#f0faf0]' : 'border-l-[#2da0a4] bg-[#f0fafa]'
            }`}>
              <div className={`text-xs font-bold uppercase mb-1 ${
                summary.scope === 'universal' ? 'text-green-700' : 'text-[#2da0a4]'
              }`}>{summary.scope}</div>
              <div className="font-semibold text-sm text-gray-900 mb-1">{summary.topic}</div>
              <p className="text-sm text-gray-700">{summary.summary}</p>
            </div>
          ))}
        </main>
      </div>
    </div>
  );
}
