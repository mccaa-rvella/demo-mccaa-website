import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTopSectors, useAllSectors } from '../hooks/useSectors';
import SectorCard from '../components/ui/SectorCard';
import SearchBar from './SearchBar';
import AudiencePicker from './AudiencePicker';
import { apiFetch } from '../api/client';

interface PickerState {
  sectorName: string;
  businessSlug: string;
  consumerSlug: string;
}

export default function KBLanding() {
  const { data: topSectors } = useTopSectors();
  const { data: allSectors } = useAllSectors();
  const navigate = useNavigate();
  const [picker, setPicker] = useState<PickerState | null>(null);

  const handleSectorClick = useCallback(async (slug: string) => {
    const sector = allSectors?.find(s => s.slug === slug) ?? topSectors?.find(s => s.slug === slug);
    if (!sector) return;

    apiFetch('/track/visit', { method: 'POST', body: JSON.stringify({ sector: slug }) }).catch(() => {});

    if (sector.has_business && sector.has_consumer) {
      const [bizArticle, conArticle] = await Promise.all([
        apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=business`).catch(() => null),
        apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=consumer`).catch(() => null),
      ]);
      setPicker({
        sectorName: sector.name,
        businessSlug: bizArticle?.slug ?? slug,
        consumerSlug: conArticle?.slug ?? slug,
      });
    } else {
      const audience = sector.has_consumer ? 'consumer' : 'business';
      try {
        const article = await apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=${audience}`);
        navigate(`/kb/${article.slug}`);
      } catch {
        navigate(`/kb/${slug}`);
      }
    }
  }, [allSectors, topSectors, navigate]);

  const handleAudienceSelect = (slug: string) => {
    setPicker(null);
    navigate(`/kb/${slug}`);
  };

  const topSlugs = new Set(topSectors?.map(s => s.slug) ?? []);
  const remainingSectors = allSectors?.filter(s => !topSlugs.has(s.slug)) ?? [];

  return (
    <div className="pt-24">
      <section className="bg-gradient-to-br from-[#2da0a4] to-[#258487] py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">MCCAA Knowledge Base</h1>
          <p className="text-white/70 mb-8">Find regulations, standards, and consumer rights information</p>
          <SearchBar />
        </div>
      </section>

      {topSectors && topSectors.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 -mt-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {topSectors.map(s => (
              <SectorCard key={s.slug} name={s.name} slug={s.slug} hasBusiness={s.has_business}
                hasConsumer={s.has_consumer} visitCount={s.visit_count} featured onClick={handleSectorClick} />
            ))}
          </div>
        </section>
      )}

      <section className="max-w-5xl mx-auto px-4 py-12">
        <h2 className="text-lg font-bold text-gray-900 mb-4">All Sectors</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {remainingSectors.map(s => (
            <SectorCard key={s.slug} name={s.name} slug={s.slug} hasBusiness={s.has_business}
              hasConsumer={s.has_consumer} onClick={handleSectorClick} />
          ))}
        </div>
      </section>

      {picker && (
        <AudiencePicker sectorName={picker.sectorName} businessSlug={picker.businessSlug}
          consumerSlug={picker.consumerSlug} onSelect={handleAudienceSelect} onClose={() => setPicker(null)} />
      )}
    </div>
  );
}
