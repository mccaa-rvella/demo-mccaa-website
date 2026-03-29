import { useState, useEffect } from 'react';
import { ArrowLeft, ChevronDown, ChevronUp, Search, Building2, Truck, ShoppingBag, PackageCheck, Shield, Warehouse, BookOpen } from 'lucide-react';

/* ── Loader ── */
const spinCss = `@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}`;
const Loader = ({ size = 32, label = '' }: { size?: number; label?: string }) => (
  <>
    <style>{spinCss}</style>
    <div style={{ textAlign: 'center', padding: '3rem 0' }}>
      <div style={{ width: size, height: size, border: '3px solid rgba(45,160,164,0.15)', borderTop: '3px solid #2da0a4', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem' }} />
      {label && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>{label}</p>}
    </div>
  </>
);

/* ── Constants ── */
const PILLARS = [
  { id: 'technical', label: 'Technical Regulations', icon: '🔧', desc: 'Product safety, CE marking, directives' },
  { id: 'competition', label: 'Competition', icon: '⚖️', desc: 'Anti-trust, mergers, market dominance' },
  { id: 'consumer', label: 'Consumer Protection', icon: '🛡️', desc: 'Returns, guarantees, unfair practices' },
  { id: 'standardisation', label: 'Standardisation', icon: '📐', desc: 'Harmonised standards, metrology, SMI' },
];

const PILLAR_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  technical:      { bg: '#ecfeff', text: '#0e7490', border: '#a5f3fc' },
  competition:    { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  consumer:       { bg: '#f0fdf4', text: '#166534', border: '#bbf7d0' },
  standardisation:{ bg: '#ede9fe', text: '#5b21b6', border: '#c4b5fd' },
  all:            { bg: '#f3f4f6', text: '#374151', border: '#e5e7eb' },
};

const ROLES_TOP = [
  { id: 'manufacturer', label: 'Manufacturer', desc: 'You design & produce products', icon: <Building2 size={20} /> },
  { id: 'importer',     label: 'Importer',     desc: 'You bring products into the EU',  icon: <Truck size={20} /> },
  { id: 'distributor',  label: 'Distributor / Retailer', desc: 'You sell to end consumers', icon: <ShoppingBag size={20} /> },
];
const ROLES_MORE = [
  { id: 'authorised-rep', label: 'Authorised Representative', desc: 'Acting on behalf of a non-EU manufacturer', icon: <PackageCheck size={20} /> },
  { id: 'cab',            label: 'Conformity Assessment Body', desc: 'Testing & certifying products', icon: <Shield size={20} /> },
  { id: 'fsp',            label: 'Fulfilment Service Provider', desc: 'Storage/shipping for online sellers', icon: <Warehouse size={20} /> },
];

interface SectorItem { name: string; slug: string; showcase: boolean; }
interface SynthesisResult {
  title: string;
  html: string;
  meta: { sector: string; role: string; topic: string; topic_id: string; doc_count: number; };
  read_more: { pillar: string; pillar_label: string; summary: string; doc_count: number; }[];
}

export default function WizardClient() {
  // Step state
  const [step, setStep] = useState(1);
  const [sectors, setSectors] = useState<SectorItem[]>([]);
  const [showAllSectors, setShowAllSectors] = useState(false);
  const [showOtherSector, setShowOtherSector] = useState(false);
  const [customSector, setCustomSector] = useState('');
  const [showMoreRoles, setShowMoreRoles] = useState(false);

  // Selections
  const [selectedSector, setSelectedSector] = useState('');
  const [selectedSectorLabel, setSelectedSectorLabel] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedRoleLabel, setSelectedRoleLabel] = useState('');

  // Synthesis viewer state
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerLoading, setViewerLoading] = useState(false);
  const [viewerData, setViewerData] = useState<SynthesisResult | null>(null);
  const [viewerTopic, setViewerTopic] = useState('');

  // Scroll to top on step change
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }, [step]);

  // Fetch sectors
  useEffect(() => {
    fetch('http://localhost:8000/wizard/sectors')
      .then(r => r.json())
      .then(d => setSectors(d.sectors || []))
      .catch(() => setSectors([
        { name: 'Toys', slug: 'toys', showcase: true },
        { name: 'Electrical & Electronic Equipment', slug: 'electrical', showcase: true },
        { name: 'General Consumer Products', slug: 'consumer-products', showcase: true },
      ]));
  }, []);

  const selectSector = (slug: string, label: string) => {
    setSelectedSector(slug); setSelectedSectorLabel(label); setStep(2);
  };

  const selectRole = (id: string, label: string) => {
    setSelectedRole(id); setSelectedRoleLabel(label); setStep(3);
  };

  const openSynthesis = async (topicId: string, topicLabel: string) => {
    setViewerTopic(topicId);
    setViewerOpen(true);
    setViewerLoading(true);
    setViewerData(null);
    try {
      const res = await fetch('http://localhost:8000/wizard/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sector: selectedSector, sector_label: selectedSectorLabel,
          role: selectedRole, role_label: selectedRoleLabel,
          topic: topicId, topic_label: topicLabel,
        }),
      });
      if (!res.ok) throw new Error('Failed');
      setViewerData(await res.json());
    } catch {
      setViewerData({
        title: `${topicLabel} — ${selectedSectorLabel}`,
        html: '<p>Failed to generate the compliance briefing. Please try again.</p>',
        meta: { sector: selectedSectorLabel, role: selectedRoleLabel, topic: topicLabel, topic_id: topicId, doc_count: 0 },
        read_more: [],
      });
    } finally {
      setViewerLoading(false);
    }
  };

  const closeViewer = () => { setViewerOpen(false); setViewerData(null); };

  const resetWizard = () => {
    setStep(1); setSelectedSector(''); setSelectedSectorLabel('');
    setSelectedRole(''); setSelectedRoleLabel('');
    setShowAllSectors(false); setShowOtherSector(false); setCustomSector('');
    setShowMoreRoles(false); closeViewer();
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.875rem 1rem', borderRadius: '12px',
    background: '#f9fafb', border: '1.5px solid #e5e7eb', color: '#111827',
    fontSize: '0.95rem', outline: 'none',
  };
  const ghostBtn: React.CSSProperties = {
    background: '#f9fafb', border: '1.5px solid #e5e7eb', color: '#374151',
    borderRadius: '12px', padding: '0.875rem 1.5rem', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem',
  };

  const showcaseSectors = sectors.filter(s => s.showcase);
  const otherSectors = sectors.filter(s => !s.showcase);

  const pillarC = (id: string) => PILLAR_COLORS[id] || PILLAR_COLORS.all;

  return (
    <main className="wizard-page">
      <div className="wizard-bg-overlay" />
      <section className="wizard-content-wrapper" style={{ paddingTop: '8rem', paddingBottom: '4rem' }}>

        {/* Header */}
        <div className="wizard-header">
          <h1>Compliance Wizard</h1>
          <p>Find the exact regulations that apply to your business in 3 steps.</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
            {[1, 2, 3].map(s => (
              <div key={s} style={{
                width: s === step ? 32 : 10, height: 10, borderRadius: 999,
                background: s <= step ? '#2da0a4' : '#e5e7eb', transition: 'all 0.3s ease',
              }} />
            ))}
          </div>
        </div>

        <div className="glass-panel">

          {/* ── STEP 1: SECTOR ── */}
          {step === 1 && (
            <div className="wizard-step animation-fade-in">
              <h2>Step 1 — What sector do you operate in?</h2>
              <p style={{ color: '#6b7280', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Select the product or service sector most relevant to your business.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                {showcaseSectors.map(s => (
                  <button key={s.slug} className="wizard-btn option-btn" onClick={() => selectSector(s.slug, s.name)}
                    style={{ fontWeight: 700, padding: '1.25rem', fontSize: '1rem' }}>
                    {s.name}
                  </button>
                ))}
              </div>

              {!showAllSectors && !showOtherSector && (
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                  <button className="wizard-btn" onClick={() => setShowAllSectors(true)}
                    style={{ flex: 1, justifyContent: 'center', border: '1.5px dashed #d1d5db', color: '#6b7280' }}>
                    <ChevronDown size={16} /> Browse all sectors
                  </button>
                  <button className="wizard-btn" onClick={() => setShowOtherSector(true)}
                    style={{ flex: 1, justifyContent: 'center', border: '1.5px dashed #d1d5db', color: '#6b7280' }}>
                    <Search size={16} /> My sector isn't listed
                  </button>
                </div>
              )}

              {showAllSectors && (
                <div className="animation-fade-in" style={{ marginTop: '1rem' }}>
                  <button className="btn-text" onClick={() => setShowAllSectors(false)}><ChevronUp size={14} /> Hide</button>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.65rem', marginTop: '0.5rem' }}>
                    {otherSectors.map(s => (
                      <button key={s.slug} className="wizard-btn option-btn" onClick={() => selectSector(s.slug, s.name)}>{s.name}</button>
                    ))}
                  </div>
                </div>
              )}

              {showOtherSector && (
                <div className="animation-fade-in" style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <input type="text" value={customSector} onChange={e => setCustomSector(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && customSector.trim() && selectSector(customSector.toLowerCase().replace(/\s+/g, '-'), customSector)}
                    placeholder="e.g. Pharmaceutical distribution, Aviation services..." style={inputStyle} autoFocus />
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button style={ghostBtn} onClick={() => setShowOtherSector(false)}>← Back</button>
                    <button className="wizard-btn action-primary" style={{ flex: 1, marginTop: 0 }}
                      onClick={() => customSector.trim() && selectSector(customSector.toLowerCase().replace(/\s+/g, '-'), customSector)}
                      disabled={!customSector.trim()}>Continue</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── STEP 2: ROLE ── */}
          {step === 2 && (
            <div className="wizard-step animation-fade-in">
              <button className="btn-text" onClick={() => setStep(1)}><ArrowLeft size={14} /> Change sector</button>
              <div style={{ display: 'inline-block', padding: '0.3rem 0.85rem', borderRadius: '999px', background: '#ecfeff', color: '#0e7490', fontSize: '0.8rem', fontWeight: 600, marginBottom: '1rem' }}>
                {selectedSectorLabel}
              </div>
              <h2>Step 2 — What is your role in the supply chain?</h2>

              <div style={{ display: 'grid', gap: '0.65rem' }}>
                {ROLES_TOP.map(r => (
                  <button key={r.id} className="wizard-btn option-btn" onClick={() => selectRole(r.id, r.label)}
                    style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.1rem 1.25rem' }}>
                    <div style={{ width: 40, height: 40, borderRadius: '12px', background: '#f0fdfa', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2da0a4', flexShrink: 0 }}>
                      {r.icon}
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 700, color: '#111827' }}>{r.label}</div>
                      <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>{r.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
              {!showMoreRoles ? (
                <button className="wizard-btn" onClick={() => setShowMoreRoles(true)}
                  style={{ width: '100%', justifyContent: 'center', marginTop: '0.75rem', border: '1.5px dashed #d1d5db', color: '#6b7280' }}>
                  <ChevronDown size={16} /> Other roles
                </button>
              ) : (
                <div className="animation-fade-in" style={{ marginTop: '0.75rem', display: 'grid', gap: '0.65rem' }}>
                  {ROLES_MORE.map(r => (
                    <button key={r.id} className="wizard-btn option-btn" onClick={() => selectRole(r.id, r.label)}
                      style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.1rem 1.25rem' }}>
                      <div style={{ width: 40, height: 40, borderRadius: '12px', background: '#f0fdfa', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2da0a4', flexShrink: 0 }}>
                        {r.icon}
                      </div>
                      <div style={{ textAlign: 'left' }}>
                        <div style={{ fontWeight: 700, color: '#111827' }}>{r.label}</div>
                        <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>{r.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── STEP 3: TOPIC ── */}
          {step === 3 && (
            <div className="wizard-step animation-fade-in">
              <button className="btn-text" onClick={() => setStep(2)}><ArrowLeft size={14} /> Change role</button>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                <span style={{ padding: '0.3rem 0.85rem', borderRadius: '999px', background: '#ecfeff', color: '#0e7490', fontSize: '0.8rem', fontWeight: 600 }}>{selectedSectorLabel}</span>
                <span style={{ padding: '0.3rem 0.85rem', borderRadius: '999px', background: '#f0fdf4', color: '#166534', fontSize: '0.8rem', fontWeight: 600 }}>{selectedRoleLabel}</span>
              </div>
              <h2>Step 3 — What topic are you interested in?</h2>
              <p style={{ color: '#6b7280', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Select a topic and we'll generate a tailored compliance briefing for you.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                {PILLARS.map(p => {
                  const c = pillarC(p.id);
                  return (
                    <button key={p.id} onClick={() => openSynthesis(p.id, p.label)}
                      style={{
                        background: '#fff', border: `2px solid ${c.border}`, borderRadius: '20px',
                        padding: '1.5rem 1.25rem', cursor: 'pointer', textAlign: 'center',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = c.bg; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.transform = 'translateY(0)'; }}>
                      <span style={{ fontSize: '2rem' }}>{p.icon}</span>
                      <span style={{ fontWeight: 700, color: '#111827', fontSize: '0.95rem' }}>{p.label}</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', lineHeight: 1.4 }}>{p.desc}</span>
                    </button>
                  );
                })}
              </div>

              <button className="wizard-btn action-primary" onClick={() => openSynthesis('all', 'All Topics')} style={{ marginTop: '1rem' }}>
                Show me everything — all topics
              </button>

              <button className="btn-text" onClick={resetWizard} style={{ display: 'block', margin: '1.5rem auto 0' }}>
                ← Start over
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ── SYNTHESIS SOURCE VIEWER ── */}
      {viewerOpen && (
        <>
          {/* Backdrop */}
          <div onClick={closeViewer}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 200, backdropFilter: 'blur(3px)' }} />

          {/* Full-height drawer */}
          <div style={{
            position: 'fixed', top: 0, right: 0, bottom: 0,
            width: 'min(780px, 97vw)', background: '#fff',
            boxShadow: '-12px 0 48px rgba(0,0,0,0.18)', zIndex: 201,
            display: 'flex', flexDirection: 'column', borderRadius: '28px 0 0 28px',
          }}>
            {/* Header */}
            <div style={{
              padding: '1.25rem 1.75rem', borderBottom: '1px solid #e5e7eb',
              background: '#f9fafb', borderRadius: '28px 0 0 0',
              display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem',
            }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', flex: 1, minWidth: 0 }}>
                {/* MCCAA logo badge */}
                <div style={{
                  width: 36, height: 36, borderRadius: '10px', background: '#2da0a4', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span style={{ color: '#fff', fontWeight: 800, fontSize: '14px' }}>M</span>
                </div>
                <div style={{ minWidth: 0 }}>
                  <p style={{ fontSize: '0.7rem', color: '#6b7280', margin: 0, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    MCCAA Compliance Briefing
                  </p>
                  <p style={{ fontWeight: 700, color: '#111827', fontSize: '0.95rem', margin: '2px 0 0', lineHeight: 1.3 }}>
                    {viewerLoading ? 'Generating your briefing...' : viewerData?.title || ''}
                  </p>
                  {/* Breadcrumb badges */}
                  {(selectedSectorLabel || selectedRoleLabel || viewerTopic) && (
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginTop: '0.4rem' }}>
                      {selectedSectorLabel && <span style={{ padding: '0.1rem 0.55rem', borderRadius: '999px', background: '#ecfeff', color: '#0e7490', fontSize: '0.68rem', fontWeight: 600 }}>{selectedSectorLabel}</span>}
                      {selectedRoleLabel && <span style={{ padding: '0.1rem 0.55rem', borderRadius: '999px', background: '#f0fdf4', color: '#166534', fontSize: '0.68rem', fontWeight: 600 }}>{selectedRoleLabel}</span>}
                      {viewerTopic && (() => { const c = pillarC(viewerTopic); return <span style={{ padding: '0.1rem 0.55rem', borderRadius: '999px', background: c.bg, color: c.text, fontSize: '0.68rem', fontWeight: 600 }}>{PILLARS.find(p => p.id === viewerTopic)?.label || 'All Topics'}</span>; })()}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                <button onClick={() => setStep(3)} style={{ padding: '0.4rem 0.85rem', borderRadius: '8px', background: '#f3f4f6', border: '1px solid #e5e7eb', cursor: 'pointer', color: '#374151', fontSize: '0.8rem', fontWeight: 600 }}>
                  ← Back
                </button>
                <button onClick={closeViewer} style={{
                  width: 34, height: 34, borderRadius: '8px', background: '#f3f4f6', border: '1px solid #e5e7eb',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#6b7280', fontSize: '1.1rem',
                }}>✕</button>
              </div>
            </div>

            {/* Brand strip */}
            <div style={{ height: 3, display: 'flex', flexShrink: 0 }}>
              {['#2da0a4', '#7a4a5f', '#d68f49', '#e5ca6d', '#b8e38d'].map((c, i) => (
                <div key={i} style={{ flex: 1, background: c }} />
              ))}
            </div>

            {/* Scrollable content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem 2.5rem' }}>
              {viewerLoading ? (
                <Loader size={44} label={`Generating your ${PILLARS.find(p => p.id === viewerTopic)?.label || ''} compliance briefing using Claude AI...`} />
              ) : viewerData ? (
                <>
                  {/* Main article */}
                  <article>
                    <div className="html-content" dangerouslySetInnerHTML={{ __html: viewerData.html }} />
                  </article>

                  {/* Read More section */}
                  {viewerData.read_more?.length > 0 && (
                    <div style={{ marginTop: '3rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
                        <BookOpen size={18} style={{ color: '#6b7280' }} />
                        <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
                          Also Relevant to You
                        </h3>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                        {viewerData.read_more.map(rm => {
                          const c = pillarC(rm.pillar);
                          const pillar = PILLARS.find(p => p.id === rm.pillar);
                          return (
                            <button key={rm.pillar}
                              onClick={() => openSynthesis(rm.pillar, rm.pillar_label)}
                              style={{
                                background: '#fff', border: `1.5px solid ${c.border}`, borderRadius: '16px',
                                padding: '1.25rem', cursor: 'pointer', textAlign: 'left',
                                transition: 'all 0.15s ease',
                              }}
                              onMouseEnter={e => { e.currentTarget.style.background = c.bg; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                              onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.transform = 'translateY(0)'; }}>
                              <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{pillar?.icon || '📄'}</div>
                              <div style={{ fontWeight: 700, color: c.text, fontSize: '0.85rem', marginBottom: '0.35rem' }}>{rm.pillar_label}</div>
                              <div style={{ fontSize: '0.75rem', color: '#6b7280', lineHeight: 1.5 }}>
                                {rm.summary.replace(/<[^>]*>/g, '').slice(0, 100)}...
                              </div>
                              <div style={{ marginTop: '0.75rem', fontSize: '0.72rem', fontWeight: 600, color: c.text }}>
                                Read briefing →
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* New search */}
                  <div style={{ marginTop: '2.5rem', textAlign: 'center' }}>
                    <button onClick={resetWizard} className="wizard-btn action-primary">Start a new search</button>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </>
      )}
    </main>
  );
}
