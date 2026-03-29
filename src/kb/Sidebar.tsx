import TagPill from '../components/ui/TagPill';

interface SidebarProps {
  topics: string[];
  actors: string[];
  crossCuttingSummaries: Array<{ topic: string; scope: string; article_slug: string }>;
  activeTag: string | null;
  audience: string;
  onTagClick: (tag: string) => void;
}

export default function Sidebar({ topics, actors, crossCuttingSummaries, activeTag, audience, onTagClick }: SidebarProps) {
  return (
    <aside className="w-56 flex-shrink-0 hidden lg:block">
      <div className="sticky top-28 space-y-6">
        <div>
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Topics</div>
          <div className="flex flex-wrap gap-2">
            {topics.map(t => (
              <TagPill key={t} label={t} type="topic" active={activeTag === t} onClick={() => onTagClick(t)} />
            ))}
          </div>
        </div>
        {audience === 'business' && actors.length > 0 && (
          <div>
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Actors</div>
            <div className="flex flex-wrap gap-2">
              {actors.map(a => (
                <TagPill key={a} label={a} type="actor" active={activeTag === a} onClick={() => onTagClick(a)} />
              ))}
            </div>
          </div>
        )}
        {crossCuttingSummaries.length > 0 && (
          <div>
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Related Topics</div>
            <div className="space-y-2">
              {crossCuttingSummaries.map((s, i) => (
                <div key={i} className="bg-gray-50 rounded-lg p-3">
                  <div className="font-semibold text-sm text-gray-900">{s.topic}</div>
                  <div className="text-xs text-gray-500 capitalize">{s.scope}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
