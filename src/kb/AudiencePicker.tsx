import { motion, AnimatePresence } from 'motion/react';
import { Briefcase, User, X } from 'lucide-react';

interface AudiencePickerProps {
  sectorName: string;
  businessSlug: string;
  consumerSlug: string;
  onSelect: (slug: string) => void;
  onClose: () => void;
}

export default function AudiencePicker({ sectorName, businessSlug, consumerSlug, onSelect, onClose }: AudiencePickerProps) {
  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full" onClick={e => e.stopPropagation()}>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">{sectorName}</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
          </div>
          <p className="text-gray-600 text-sm mb-6">Are you looking for information as a business or as a consumer?</p>
          <div className="flex gap-4">
            <button onClick={() => onSelect(businessSlug)}
              className="flex-1 flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-[#2da0a4] hover:bg-[#2da0a4]/5 transition-all">
              <Briefcase size={32} className="text-[#2da0a4]" />
              <span className="font-semibold text-gray-900">Business</span>
              <span className="text-xs text-gray-500">Compliance & regulations</span>
            </button>
            <button onClick={() => onSelect(consumerSlug)}
              className="flex-1 flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-[#7a4a5f] hover:bg-[#7a4a5f]/5 transition-all">
              <User size={32} className="text-[#7a4a5f]" />
              <span className="font-semibold text-gray-900">Consumer</span>
              <span className="text-xs text-gray-500">Your rights & safety</span>
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
