interface SectorCardProps {
  name: string;
  slug: string;
  hasBusiness: boolean;
  hasConsumer: boolean;
  visitCount?: number;
  featured?: boolean;
  onClick: (slug: string) => void;
}

export default function SectorCard({ name, slug, hasBusiness, hasConsumer, visitCount, featured, onClick }: SectorCardProps) {
  return (
    <button
      onClick={() => onClick(slug)}
      className={`text-left rounded-xl border transition-all hover:shadow-md hover:border-[#2da0a4]/50 ${
        featured
          ? 'bg-white border-[#2da0a4]/30 p-5 shadow-sm'
          : 'bg-white border-gray-200 p-4'
      }`}
    >
      <div className={`font-bold text-gray-900 ${featured ? 'text-lg' : 'text-sm'}`}>{name}</div>
      <div className="flex gap-2 mt-2">
        {hasBusiness && (
          <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Business</span>
        )}
        {hasConsumer && (
          <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Consumer</span>
        )}
      </div>
      {featured && visitCount != null && (
        <div className="text-xs text-gray-400 mt-2">{visitCount} visits</div>
      )}
    </button>
  );
}
