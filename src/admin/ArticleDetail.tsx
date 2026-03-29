import { CheckCircle, XCircle } from 'lucide-react';

interface ArticleDetailProps {
  article: {
    id: number;
    title: string;
    sector: string;
    audience: string;
    status: string;
    html_content: string;
    skills_used: string[];
    source_knowledge_unit_ids: number[];
  };
  onApprove: () => void;
  onReject: () => void;
  isApproving: boolean;
  isRejecting: boolean;
}

export default function ArticleDetail({ article, onApprove, onReject, isApproving, isRejecting }: ArticleDetailProps) {
  const canApprove = article.status === 'draft' || article.status === 'update_pending';
  const canReject = article.status === 'draft' || article.status === 'update_pending';

  return (
    <div className="border-t-2 border-[#2da0a4] bg-gray-50 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-500">
          Skills: {article.skills_used.length > 0 ? article.skills_used.join(', ') : 'none'} |
          Sources: {article.source_knowledge_unit_ids.length} knowledge units
        </div>
        <div className="flex gap-3">
          {canApprove && (
            <button onClick={onApprove} disabled={isApproving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors">
              <CheckCircle size={16} /> {isApproving ? 'Approving...' : 'Approve'}
            </button>
          )}
          {canReject && (
            <button onClick={onReject} disabled={isRejecting}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors">
              <XCircle size={16} /> {isRejecting ? 'Rejecting...' : 'Reject'}
            </button>
          )}
        </div>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6 max-h-96 overflow-y-auto">
        <div dangerouslySetInnerHTML={{ __html: article.html_content }} className="prose prose-sm max-w-none" />
      </div>
    </div>
  );
}
