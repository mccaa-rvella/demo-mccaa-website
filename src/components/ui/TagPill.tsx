const TOPIC_COLOURS: Record<string, { bg: string; text: string }> = {
  technical: { bg: 'bg-[#2da0a4]', text: 'text-white' },
  consumer: { bg: 'bg-[#7a4a5f]', text: 'text-white' },
  standardisation: { bg: 'bg-[#d68f49]', text: 'text-white' },
  competition: { bg: 'bg-[#e5ca6d]', text: 'text-gray-800' },
};

const ACTOR_STYLE = { bg: 'bg-[#64748b]', text: 'text-white' };

interface TagPillProps {
  label: string;
  type: 'topic' | 'actor';
  active?: boolean;
  onClick?: () => void;
}

export default function TagPill({ label, type, active = false, onClick }: TagPillProps) {
  const style = type === 'topic'
    ? TOPIC_COLOURS[label.toLowerCase()] ?? TOPIC_COLOURS.technical
    : ACTOR_STYLE;

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all cursor-pointer
        ${style.bg} ${style.text} ${active ? 'ring-2 ring-offset-1 ring-gray-900' : 'opacity-80 hover:opacity-100'}`}
    >
      {label}
    </button>
  );
}
