"""
MCCAA Knowledge Base Seeder
Seeds the database with structured content for all 12 sectors,
4 pillars, cross-cutting topics, and universal content.

Uses direct DB insertion (no admin API needed, no embedding for speed).
Embeddings can be regenerated later.

Run from host: PGPASSWORD=mysecretpassword python3 seed_kb.py
Or adjust for Docker exec.
"""
import json
import sys

# We'll generate SQL INSERT statements to run via psql
# since the host can't pip install psycopg2

DOCUMENTS = []

def add(title, content, sector=None, pillar="technical", roles=None, scope="sector-specific", 
        legal_basis=None, topic_tags=None, url=""):
    """Add a document to the list."""
    slug = title.lower().strip()
    for ch in "(),.'\"":
        slug = slug.replace(ch, "")
    slug = slug.replace(" & ", "-").replace("&", "-").replace(" ", "-").replace("--", "-")[:80]
    
    DOCUMENTS.append({
        "title": title,
        "content": content,
        "sector": sector,
        "pillar": pillar,
        "roles": roles or ["all"],
        "scope": scope,
        "slug": slug,
        "legal_basis": legal_basis,
        "topic_tags": topic_tags or [],
        "url": url,
    })

# ═══════════════════════════════════════════════════════════════
# UNIVERSAL CONTENT (always shown)
# ═══════════════════════════════════════════════════════════════

add(
    title="Competition Law in Malta",
    content="""<h3>Overview</h3>
<p>The <strong>Malta Competition and Consumer Affairs Authority (MCCAA)</strong> enforces competition law in Malta under the <strong>Competition Act (Cap. 379)</strong>, aligned with EU competition rules (Articles 101 and 102 TFEU).</p>
<h3>Key Prohibitions</h3>
<ul>
<li><strong>Anti-competitive agreements</strong> — Agreements between businesses that prevent, restrict or distort competition (e.g., price-fixing, market-sharing, bid-rigging)</li>
<li><strong>Abuse of dominant position</strong> — A dominant firm must not exploit its market power through unfair pricing, refusal to deal, or exclusionary practices</li>
<li><strong>Merger control</strong> — Concentrations that substantially lessen competition may be prohibited or subject to conditions</li>
</ul>
<h3>Penalties</h3>
<p>Businesses found in breach of competition law may face fines of up to <strong>10% of total turnover</strong>. Individuals who facilitate cartels may also face personal liability.</p>
<h3>Leniency Programme</h3>
<p>The MCCAA operates a leniency programme: the first member of a cartel to report it may receive full immunity from fines.</p>""",
    pillar="competition",
    scope="universal",
    legal_basis="Competition Act (Cap. 379), Articles 101-102 TFEU",
    topic_tags=["antitrust", "mergers", "cartel", "dominance"],
    url="https://mccaa.org.mt/Section/Content?contentId=2890",
)

add(
    title="Consumer Protection Essentials",
    content="""<h3>Your Rights as a Consumer in Malta</h3>
<p>All consumers in Malta are protected by the <strong>Consumer Affairs Act (Cap. 378)</strong> and EU consumer protection directives transposed into Maltese law.</p>
<h3>Key Rights</h3>
<ul>
<li><strong>Legal guarantee</strong> — All goods come with a <strong>2-year legal guarantee</strong> against lack of conformity. The seller is obliged to repair, replace, reduce the price, or refund.</li>
<li><strong>Right of withdrawal</strong> — For goods bought online or at a distance, consumers have <strong>14 days</strong> to return the product without giving a reason.</li>
<li><strong>Unfair commercial practices</strong> — Misleading advertising, aggressive selling, and bait-and-switch tactics are prohibited.</li>
<li><strong>Price indication</strong> — All products must display the selling price and the unit price clearly and unambiguously.</li>
</ul>
<h3>Filing a Complaint</h3>
<p>Consumers can file complaints with the <strong>Office for Consumer Affairs</strong> within the MCCAA. Mediation and arbitration services are available free of charge.</p>""",
    pillar="consumer",
    scope="universal",
    legal_basis="Consumer Affairs Act (Cap. 378), Directive 2011/83/EU",
    topic_tags=["guarantee", "returns", "unfair practices", "pricing"],
    url="https://mccaa.org.mt/Section/Content?contentId=1267",
)

add(
    title="General Product Safety Obligations",
    content="""<h3>General Product Safety Regulation (GPSR)</h3>
<p>The <strong>General Product Safety Regulation (EU) 2023/988</strong> applies to all consumer products not covered by sector-specific legislation. It ensures that only safe products are placed on the EU market.</p>
<h3>Key Obligations</h3>
<ul>
<li><strong>All economic operators</strong> must ensure products are safe before placing them on the market</li>
<li><strong>Risk assessment</strong> — Producers must carry out an analysis of risks posed by their products</li>
<li><strong>Traceability</strong> — Products must bear the manufacturer's name, registered trade name or trademark, and contact address</li>
<li><strong>Recall obligations</strong> — If a product is found to be dangerous, immediate corrective action is required, including notifying the authorities via <strong>Safety Gate (RAPEX)</strong></li>
</ul>
<h3>Online Sales</h3>
<p>The GPSR explicitly covers products sold online, including through online marketplaces. Marketplace operators have specific due diligence obligations.</p>""",
    pillar="technical",
    scope="universal",
    legal_basis="Regulation (EU) 2023/988 (GPSR)",
    topic_tags=["product safety", "GPSR", "recall", "traceability"],
    url="https://ec.europa.eu/safety-gate/",
)


# ═══════════════════════════════════════════════════════════════
# CROSS-CUTTING CONTENT (applies across sectors/roles)
# ═══════════════════════════════════════════════════════════════

add(
    title="CE Marking — Requirements and Obligations",
    content="""<h3>What is CE Marking?</h3>
<p>The <strong>CE marking</strong> (Conformité Européenne) indicates that a product complies with the applicable EU legislation and may be sold freely throughout the European Economic Area.</p>
<h3>Who Must Affix CE Marking?</h3>
<ul>
<li><strong>Manufacturers</strong> are responsible for affixing the CE marking after ensuring conformity and drawing up the EU Declaration of Conformity (DoC).</li>
<li><strong>Importers</strong> must verify that the manufacturer has carried out the appropriate conformity assessment procedure and that the CE marking is affixed.</li>
<li><strong>Authorised representatives</strong> may affix the CE marking on behalf of the manufacturer if mandated to do so.</li>
</ul>
<h3>Requirements</h3>
<ul>
<li>The CE marking must be at least <strong>5 mm high</strong> and maintain the correct proportions.</li>
<li>It must be visible, legible, and indelible.</li>
<li>It must be affixed to the product, its data plate, or packaging (where applicable).</li>
</ul>
<h3>Penalties</h3>
<p>Placing a product on the market without the required CE marking — or affixing it without meeting the underlying requirements — is an offence under Maltese law and may result in <strong>market surveillance action</strong>, product withdrawal, or fines.</p>""",
    scope="cross-cutting",
    roles=["manufacturer", "importer", "authorised-rep", "all"],
    legal_basis="Regulation (EC) No 765/2008, Decision No 768/2008/EC",
    topic_tags=["CE marking", "declaration of conformity", "new approach"],
    url="https://ec.europa.eu/growth/single-market/ce-marking_en",
)

add(
    title="EU Declaration of Conformity (DoC)",
    content="""<h3>What is a Declaration of Conformity?</h3>
<p>The <strong>EU Declaration of Conformity</strong> is a mandatory document in which the manufacturer (or their authorised representative) declares that the product meets all applicable EU requirements.</p>
<h3>Content Requirements</h3>
<p>The DoC must contain:</p>
<ul>
<li>Product identification (type, batch, serial number)</li>
<li>Name and address of the manufacturer (and authorised representative, if applicable)</li>
<li>Reference to the applicable harmonised standards or technical specifications used</li>
<li>Reference to the applicable EU legislation (directives/regulations)</li>
<li>Name and identification number of the Notified Body (if involved)</li>
<li>Place and date of issue, signature</li>
</ul>
<h3>Obligations per Role</h3>
<ul>
<li><strong>Manufacturers</strong> — Must draw up and sign the DoC; keep it for 10 years after the product is placed on the market.</li>
<li><strong>Importers</strong> — Must ensure the DoC is available and provide a copy to the market surveillance authority upon request.</li>
<li><strong>Distributors</strong> — Must be able to identify who supplied them the product and verify the CE marking is present.</li>
</ul>""",
    scope="cross-cutting",
    roles=["manufacturer", "importer", "authorised-rep", "all"],
    legal_basis="Decision No 768/2008/EC, Annex II/III",
    topic_tags=["declaration of conformity", "documentation", "compliance"],
    url="https://ec.europa.eu/growth/single-market/ce-marking/conformity-assessment_en",
)

add(
    title="Harmonised Standards and Presumption of Conformity",
    content="""<h3>What are Harmonised Standards?</h3>
<p><strong>Harmonised standards</strong> are European standards (EN) developed by CEN, CENELEC, or ETSI at the request of the European Commission. They provide technical specifications that, when followed, give a <strong>presumption of conformity</strong> with the essential requirements of EU legislation.</p>
<h3>Key Points</h3>
<ul>
<li>Using harmonised standards is <strong>voluntary</strong> but provides the easiest path to compliance.</li>
<li>References to harmonised standards are published in the <strong>Official Journal of the EU</strong>.</li>
<li>If you do not use harmonised standards, you must demonstrate compliance through other means (e.g., testing by a Notified Body).</li>
</ul>
<h3>In Malta</h3>
<p>The <strong>Standards and Metrology Institute (SMI)</strong>, a division of the MCCAA, is Malta's national standards body. SMI adopts European standards as Maltese standards and provides standards information services.</p>""",
    pillar="standardisation",
    scope="cross-cutting",
    roles=["all"],
    legal_basis="Regulation (EU) No 1025/2012",
    topic_tags=["harmonised standards", "CEN", "CENELEC", "presumption of conformity"],
    url="https://mccaa.org.mt/Section/Content?contentId=1413",
)

add(
    title="Market Surveillance in Malta",
    content="""<h3>Overview</h3>
<p><strong>Market surveillance</strong> ensures that products on the Maltese market comply with applicable EU legislation and do not endanger consumers, workers, or the environment.</p>
<h3>The MCCAA's Role</h3>
<p>The MCCAA is the designated <strong>market surveillance authority</strong> for most consumer and industrial products in Malta. Its inspectors carry out:</p>
<ul>
<li>Documentary checks (CE marking, DoC, technical file)</li>
<li>Physical inspections and product testing</li>
<li>Investigation of complaints and accidents</li>
<li>Border controls in cooperation with Customs</li>
</ul>
<h3>Powers</h3>
<p>Where non-compliance is found, the MCCAA may:</p>
<ul>
<li>Require corrective measures or product withdrawal/recall</li>
<li>Prohibit products from being made available on the market</li>
<li>Issue fines and penalties</li>
<li>Issue RAPEX/Safety Gate notifications for dangerous products</li>
</ul>""",
    scope="cross-cutting",
    roles=["all"],
    legal_basis="Regulation (EU) 2019/1020",
    topic_tags=["market surveillance", "inspections", "enforcement", "RAPEX"],
    url="https://mccaa.org.mt/Section/Content?contentId=2746",
)


# ═══════════════════════════════════════════════════════════════
# SECTOR-SPECIFIC: TOYS
# ═══════════════════════════════════════════════════════════════

def add_toys():
    s = "toys"
    
    add(
        title="Toy Safety Directive — Overview",
        content="""<h3>Directive 2009/48/EC on the Safety of Toys</h3>
<p>The <strong>Toy Safety Directive</strong> establishes safety requirements that toys must meet before being placed on the EU market. It covers mechanical/physical properties, flammability, chemical properties, electrical properties, hygiene, and radioactivity.</p>
<h3>Scope</h3>
<p>A 'toy' is defined as a product designed or intended for use in play by children under 14 years of age. The directive applies whether the toy is exclusively or not exclusively designed for play.</p>
<h3>Essential Safety Requirements</h3>
<ul>
<li>Toys must not jeopardise the safety or health of users or third parties</li>
<li>Specific chemical limits for substances including lead, cadmium, chromium VI, and certain fragrances</li>
<li>Warnings and age markings must be clearly visible before purchase</li>
<li>Small parts must meet choking hazard requirements</li>
</ul>""",
        sector=s, roles=["all"], legal_basis="Directive 2009/48/EC",
        topic_tags=["toy safety", "chemical limits", "age warnings"],
        url="https://ec.europa.eu/growth/sectors/toys/safety_en",
    )

    add(
        title="Toy Importers — Obligations",
        content="""<h3>Obligations of Importers of Toys</h3>
<p>Under the Toy Safety Directive, <strong>importers</strong> (those who bring toys from outside the EU onto the EU market) have specific obligations:</p>
<ul>
<li><strong>Only place compliant toys on the market</strong> — Verify the manufacturer has performed the conformity assessment, drawn up technical documentation, and affixed CE marking.</li>
<li><strong>Indicate your details on the product</strong> — Your name, registered trade name or trademark, and contact address must appear on the toy or its packaging.</li>
<li><strong>Ensure conditions during transport/storage do not compromise compliance</strong></li>
<li><strong>Keep a copy of the EU Declaration of Conformity</strong> for 10 years and ensure the technical documentation can be made available on request.</li>
<li><strong>Carry out sample testing</strong> if deemed appropriate given the risks.</li>
<li><strong>Take corrective measures if the toy is non-compliant</strong> — Immediately inform the competent authority (MCCAA) if the toy presents a risk.</li>
</ul>
<h3>Language Requirements (Malta)</h3>
<p>Warnings on toys sold in Malta must be provided in both <strong>Maltese and English</strong>. This is a national transposition requirement.</p>""",
        sector=s, roles=["importer"], legal_basis="Directive 2009/48/EC, Art. 6",
        topic_tags=["importer obligations", "labelling", "language requirements"],
        url="https://ec.europa.eu/growth/sectors/toys/safety_en",
    )

    add(
        title="Toy Manufacturers — Obligations",
        content="""<h3>Obligations of Manufacturers of Toys</h3>
<p>Manufacturers bear the primary responsibility for toy safety:</p>
<ul>
<li><strong>Design and produce toys in compliance</strong> with the essential safety requirements in Annex II of the Directive.</li>
<li><strong>Perform conformity assessment</strong> — Internal production control (Module A) or EC-type examination (Module B + C, D, or E) for certain requirements.</li>
<li><strong>Draw up technical documentation</strong> — Including risk assessment, test reports, and the EU Declaration of Conformity.</li>
<li><strong>Affix CE marking</strong> to each toy before placing it on the market.</li>
<li><strong>Include required markings</strong> — Type, batch, serial number, manufacturer name and address.</li>
<li><strong>Maintain records</strong> — Keep technical documentation and DoC for 10 years.</li>
<li><strong>Monitor and report</strong> — Carry out sample testing, investigate complaints, and notify the authorities immediately if a toy presents a risk.</li>
</ul>""",
        sector=s, roles=["manufacturer"], legal_basis="Directive 2009/48/EC, Art. 4",
        topic_tags=["manufacturer obligations", "conformity assessment", "technical file"],
        url="https://ec.europa.eu/growth/sectors/toys/safety_en",
    )

    add(
        title="Toy Distributors — Obligations",
        content="""<h3>Obligations of Distributors/Retailers of Toys</h3>
<p><strong>Distributors</strong> (including retailers) must act with due care when making toys available on the market:</p>
<ul>
<li><strong>Verify before selling</strong> — Check that the toy bears CE marking, is accompanied by required documents (in the required languages), and that the manufacturer and importer have complied with their obligations.</li>
<li><strong>Do not supply non-compliant toys</strong> — If you have reason to believe a toy does not comply, do not make it available until it has been brought into conformity.</li>
<li><strong>Storage and transport</strong> — Ensure conditions do not jeopardise compliance.</li>
<li><strong>Cooperate with authorities</strong> — Upon request, provide all information and documentation to demonstrate conformity.</li>
<li><strong>Recall cooperation</strong> — Cooperate with manufacturers, importers, and MCCAA in any corrective measures, product withdrawal, or recall.</li>
</ul>""",
        sector=s, roles=["distributor"], legal_basis="Directive 2009/48/EC, Art. 7",
        topic_tags=["distributor obligations", "due care", "retailer"],
        url="https://ec.europa.eu/growth/sectors/toys/safety_en",
    )

add_toys()


# ═══════════════════════════════════════════════════════════════
# SECTOR-SPECIFIC: ELECTRICAL & ELECTRONIC EQUIPMENT
# ═══════════════════════════════════════════════════════════════

def add_electrical():
    s = "electrical"

    add(
        title="Low Voltage Directive (LVD) — Overview",
        content="""<h3>Directive 2014/35/EU — Low Voltage</h3>
<p>The <strong>Low Voltage Directive</strong> covers electrical equipment designed for use with voltage between <strong>50 and 1000 V AC</strong> or <strong>75 and 1500 V DC</strong>. It ensures the safety of electrical products on the EU market.</p>
<h3>Essential Requirements</h3>
<ul>
<li>Protection against electrical, mechanical, chemical, and thermal hazards</li>
<li>Protection against non-mechanical hazards (noise, vibration, ergonomic factors)</li>
<li>Insulation appropriate to foreseeable conditions</li>
</ul>
<h3>Conformity Assessment</h3>
<p>Internal production control (Module A) — manufacturers self-certify using harmonised standards (EN 60335, EN 62368, etc.).</p>""",
        sector=s, roles=["all"], legal_basis="Directive 2014/35/EU",
        topic_tags=["LVD", "electrical safety", "low voltage"],
        url="https://ec.europa.eu/growth/sectors/electrical-engineering/lvd-directive_en",
    )

    add(
        title="EMC Directive — Electromagnetic Compatibility",
        content="""<h3>Directive 2014/30/EU — EMC</h3>
<p>The <strong>Electromagnetic Compatibility Directive</strong> ensures that electrical and electronic equipment does not generate excessive electromagnetic disturbance and can function in its electromagnetic environment.</p>
<h3>Essential Requirements</h3>
<ul>
<li><strong>Emissions</strong> — Equipment must not generate electromagnetic disturbances exceeding the level above which radio and telecommunications equipment or other equipment cannot operate as intended.</li>
<li><strong>Immunity</strong> — Equipment must have a level of immunity to electromagnetic disturbance to be expected in its intended use that allows it to operate without unacceptable degradation.</li>
</ul>
<h3>Applicable Products</h3>
<p>Virtually all electrical/electronic equipment: appliances, IT equipment, industrial machinery, lighting, audio-visual equipment, etc.</p>""",
        sector=s, roles=["all"], legal_basis="Directive 2014/30/EU",
        topic_tags=["EMC", "electromagnetic", "emissions", "immunity"],
        url="https://ec.europa.eu/growth/sectors/electrical-engineering/emc-directive_en",
    )

    add(
        title="Energy Labelling & Ecodesign (EPREL)",
        content="""<h3>EU Energy Labelling</h3>
<p>Energy-related products sold in the EU must display an <strong>energy label</strong> (A to G scale) and be registered in the <strong>EPREL</strong> (European Product Registry for Energy Labelling) database.</p>
<h3>Key Requirements</h3>
<ul>
<li><strong>Manufacturers/importers</strong> must register products in EPREL before placing them on the market</li>
<li><strong>Dealers/retailers</strong> must display the energy label next to the product at the point of sale (including online)</li>
<li><strong>Ecodesign requirements</strong> set minimum energy efficiency thresholds — non-compliant products cannot be sold</li>
</ul>
<h3>Product Categories</h3>
<p>Refrigerators, washing machines, dishwashers, TVs and displays, light sources, air conditioners, tumble dryers, and more.</p>""",
        sector=s, roles=["all"], legal_basis="Regulation (EU) 2017/1369, Directive 2009/125/EC",
        topic_tags=["EPREL", "energy label", "ecodesign", "efficiency"],
        url="https://ec.europa.eu/info/energy-climate-change-environment/standards-tools-and-labels/products-labelling-rules-and-requirements/energy-label-and-ecodesign/about_en",
    )

    add(
        title="RoHS — Restriction of Hazardous Substances",
        content="""<h3>Directive 2011/65/EU (as amended)</h3>
<p>The <strong>RoHS Directive</strong> restricts the use of certain hazardous substances in electrical and electronic equipment to protect human health and the environment.</p>
<h3>Restricted Substances</h3>
<ul>
<li>Lead (Pb) — max 0.1%</li>
<li>Mercury (Hg) — max 0.1%</li>
<li>Cadmium (Cd) — max 0.01%</li>
<li>Hexavalent chromium (Cr VI) — max 0.1%</li>
<li>PBB and PBDE (brominated flame retardants) — max 0.1% each</li>
<li>DEHP, BBP, DBP, DIBP (phthalates) — max 0.1% each</li>
</ul>
<h3>Obligations</h3>
<p>Manufacturers must ensure EEE complies with substance restrictions, draw up technical documentation, perform internal production control, and affix CE marking.</p>""",
        sector=s, roles=["all"], legal_basis="Directive 2011/65/EU (RoHS 2)",
        topic_tags=["RoHS", "hazardous substances", "lead", "restriction"],
        url="https://ec.europa.eu/environment/topics/waste-and-recycling/rohs-directive_en",
    )

add_electrical()


# ═══════════════════════════════════════════════════════════════
# SECTOR-SPECIFIC: remaining sectors (concise overviews)
# ═══════════════════════════════════════════════════════════════

sectors_overview = {
    "consumer-products": ("General Consumer Products", "Regulation (EU) 2023/988 (GPSR)", 
        """<h3>General Product Safety Regulation</h3>
<p>The GPSR applies to all consumer products not covered by sector-specific harmonisation legislation. Manufacturers must ensure products are safe, perform risk assessments, maintain traceability, and cooperate with market surveillance authorities. Products sold online are explicitly covered, including obligations for online marketplace operators.</p>"""),
    "machinery": ("Machinery Directive", "Directive 2006/42/EC",
        """<h3>Machinery Directive 2006/42/EC</h3>
<p>The Machinery Directive covers machinery, interchangeable equipment, safety components, lifting accessories, and partly completed machinery. Manufacturers must perform risk assessment, ensure essential health and safety requirements are met, draw up technical files, issue an EU Declaration of Conformity, and affix CE marking.</p>
<p><strong>New Machinery Regulation (EU) 2023/1230</strong> will replace the Directive from 20 January 2027.</p>"""),
    "construction": ("Construction Products", "Regulation (EU) No 305/2011 (CPR)",
        """<h3>Construction Products Regulation</h3>
<p>The CPR establishes harmonised conditions for the marketing of construction products in the EU. Manufacturers must draw up a <strong>Declaration of Performance (DoP)</strong> and affix the <strong>CE marking</strong> based on a harmonised standard or European Technical Assessment (ETA). Performance must be declared for relevant essential characteristics.</p>"""),
    "medical-devices": ("Medical Devices", "Regulation (EU) 2017/745 (MDR)",
        """<h3>Medical Devices Regulation</h3>
<p>The MDR establishes a new regulatory framework for medical devices in the EU with stricter clinical evidence requirements, enhanced post-market surveillance, and a new classification system. All medical devices must bear a <strong>Unique Device Identifier (UDI)</strong> and be registered in EUDAMED.</p>"""),
    "ppe": ("Personal Protective Equipment", "Regulation (EU) 2016/425",
        """<h3>PPE Regulation</h3>
<p>The PPE Regulation applies to equipment designed to be worn or held by a person for protection against health or safety risks. PPE is classified into three categories based on risk level. Category III (protecting against mortal danger) requires EU-type examination by a Notified Body plus ongoing production quality monitoring.</p>"""),
    "radio-equipment": ("Radio Equipment", "Directive 2014/53/EU (RED)",
        """<h3>Radio Equipment Directive</h3>
<p>The RED covers all equipment that intentionally emits and/or receives radio waves for communication or radiodetermination. Requirements cover safety (LVD), EMC, and efficient use of radio spectrum. From August 2025, certain devices will also need to comply with cybersecurity requirements.</p>"""),
    "gas-appliances": ("Gas Appliances", "Regulation (EU) 2016/426",
        """<h3>Gas Appliances Regulation</h3>
<p>This regulation covers appliances burning gaseous fuels used for cooking, heating, hot water production, refrigeration, lighting, and washing. Manufacturers must carry out conformity assessment (EU-type examination for most appliances), affix CE marking, and ensure gas appliances are accompanied by technical instructions in the official language(s) of the Member State.</p>"""),
    "pressure-equipment": ("Pressure Equipment", "Directive 2014/68/EU (PED)",
        """<h3>Pressure Equipment Directive</h3>
<p>The PED applies to pressure equipment and assemblies with a maximum allowable pressure greater than 0.5 bar. Equipment is classified into four categories (I-IV) based on the hazard level, with increasing conformity assessment requirements. Category IV requires full quality assurance with Notified Body involvement.</p>"""),
    "measuring-instruments": ("Measuring Instruments", "Directive 2014/32/EU (MID)",
        """<h3>Measuring Instruments Directive</h3>
<p>The MID covers measuring instruments used in trade, health, safety, and environmental measurements: water meters, gas meters, electricity meters, heat meters, taximeters, material measures, dimensional measuring instruments, and exhaust gas analysers. Instruments must undergo conformity assessment before being placed on the market.</p>"""),
    "pyrotechnics": ("Pyrotechnic Articles", "Directive 2013/29/EU",
        """<h3>Pyrotechnic Articles Directive</h3>
<p>This directive covers fireworks (categories F1-F4), theatrical pyrotechnic articles (T1-T2), and other pyrotechnic articles (P1-P2). All pyrotechnic articles must bear CE marking and be classified by a Notified Body. Age restrictions apply (F1: 12+, F2: 16+, F3: 18+). F4 fireworks are restricted to professional use.</p>"""),
}

for slug, (name, legal, content) in sectors_overview.items():
    add(
        title=f"{name} — Overview",
        content=content,
        sector=slug,
        roles=["all"],
        legal_basis=legal,
        topic_tags=[slug, "overview"],
        url="https://ec.europa.eu/growth/single-market/goods_en",
    )
    
    # Add per-role docs for each sector
    for role_id, role_name in [("manufacturer", "Manufacturers"), ("importer", "Importers"), ("distributor", "Distributors/Retailers")]:
        add(
            title=f"{name} — Obligations for {role_name}",
            content=f"""<h3>{role_name} under {legal}</h3>
<p>As a <strong>{role_name.lower().rstrip('s')}</strong> of products covered by {name} legislation, your obligations include:</p>
<ul>
<li>Ensure products comply with all applicable essential requirements</li>
<li>{'Draw up the EU Declaration of Conformity and affix CE marking' if role_id == 'manufacturer' else 'Verify the CE marking and DoC are present' if role_id == 'importer' else 'Check the CE marking is present and required documents accompany the product'}</li>
<li>{'Maintain technical documentation for 10 years' if role_id in ('manufacturer', 'importer') else 'Be able to identify who supplied you the product'}</li>
<li>Take corrective action and notify the MCCAA immediately if the product presents a risk</li>
<li>Cooperate with the market surveillance authority (MCCAA) upon request</li>
</ul>
<p>{'In Malta, documentation and instructions must be available in Maltese and English.' if role_id == 'importer' else ''}</p>""",
            sector=slug,
            roles=[role_id],
            legal_basis=legal,
            topic_tags=[slug, role_id, "obligations"],
        )


# ═══════════════════════════════════════════════════════════════
# COMPETITION TOPICS
# ═══════════════════════════════════════════════════════════════

add(
    title="Antitrust & Cartels",
    content="""<h3>Anti-Competitive Agreements (Article 101 TFEU / Cap. 379)</h3>
<p>Agreements between businesses that restrict competition are prohibited. This includes:</p>
<ul>
<li><strong>Price-fixing</strong> — Competitors agreeing on prices</li>
<li><strong>Market-sharing</strong> — Dividing territories or customers</li>
<li><strong>Bid-rigging</strong> — Coordinating bids in public procurement</li>
<li><strong>Output restrictions</strong> — Limiting production or supply</li>
</ul>
<h3>Exemptions</h3>
<p>Certain agreements may be exempted if they improve production/distribution or promote technical/economic progress while allowing consumers a fair share of the resulting benefit.</p>
<h3>Penalties in Malta</h3>
<p>Fines up to 10% of the undertaking's total turnover for the preceding financial year.</p>""",
    pillar="competition",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Competition Act (Cap. 379), Art. 5; Article 101 TFEU",
    topic_tags=["antitrust", "cartels", "price-fixing"],
    url="https://mccaa.org.mt/Section/Content?contentId=2890",
)

add(
    title="Merger Control",
    content="""<h3>Merger Control in Malta</h3>
<p>Concentrations (mergers, acquisitions, joint ventures) that meet specific turnover thresholds must be notified to the MCCAA's <strong>Office for Competition</strong> before completion.</p>
<h3>Notification Thresholds</h3>
<p>A concentration must be notified when the combined aggregate turnover of the undertakings concerned in Malta exceeds the thresholds set in the Control of Concentrations Regulations.</p>
<h3>Assessment</h3>
<p>The MCCAA assesses whether the concentration would significantly impede effective competition in the Maltese market. It may:</p>
<ul>
<li>Approve unconditionally</li>
<li>Approve with conditions (remedies)</li>
<li>Prohibit the concentration</li>
</ul>""",
    pillar="competition",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Competition Act (Cap. 379), Part V",
    topic_tags=["mergers", "acquisitions", "concentrations"],
    url="https://mccaa.org.mt/Section/Content?contentId=2890",
)

add(
    title="Abuse of Dominant Position",
    content="""<h3>Prohibition on Abuse of Dominance</h3>
<p>An undertaking holding a <strong>dominant position</strong> in the Maltese market must not abuse that position. Abuse may include:</p>
<ul>
<li>Imposing unfair purchase or selling prices</li>
<li>Limiting production, markets, or technical development to the prejudice of consumers</li>
<li>Applying dissimilar conditions to equivalent transactions (discrimination)</li>
<li>Tying — making contracts subject to supplementary obligations unconnected to the subject</li>
<li>Predatory pricing or margin squeeze</li>
</ul>
<h3>What Constitutes Dominance?</h3>
<p>Dominance is generally presumed above 40% market share, but depends on the specific market analysis including barriers to entry, countervailing buyer power, and competitive dynamics.</p>""",
    pillar="competition",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Competition Act (Cap. 379), Art. 9; Article 102 TFEU",
    topic_tags=["dominance", "abuse", "market power"],
    url="https://mccaa.org.mt/Section/Content?contentId=2890",
)


# ═══════════════════════════════════════════════════════════════
# CONSUMER PROTECTION TOPICS
# ═══════════════════════════════════════════════════════════════

add(
    title="Returns, Refunds & Legal Guarantees",
    content="""<h3>The Legal Guarantee</h3>
<p>Under EU law transposed in Malta, all goods must conform to the contract of sale. Consumers have a <strong>2-year legal guarantee</strong> from delivery.</p>
<h3>Remedies</h3>
<p>If goods are defective or not as described, the consumer may request (in this order):</p>
<ol>
<li><strong>Repair</strong> or <strong>replacement</strong> (free of charge, within a reasonable time)</li>
<li>If repair/replacement is impossible or disproportionate: <strong>price reduction</strong> or <strong>full refund</strong></li>
</ol>
<h3>Burden of Proof</h3>
<p>During the <strong>first year</strong> after delivery, any defect is presumed to have existed at the time of delivery (the seller must prove otherwise). After 12 months, the consumer bears the burden of proof.</p>""",
    pillar="consumer",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Directive (EU) 2019/771, Consumer Affairs Act (Cap. 378)",
    topic_tags=["guarantee", "refund", "repair", "returns"],
    url="https://mccaa.org.mt/Section/Content?contentId=1267",
)

add(
    title="Online Shopping & Distance Selling Rights",
    content="""<h3>Your Rights When Buying Online</h3>
<p>Consumers purchasing goods or services at a distance (online, phone, mail order) have enhanced protections:</p>
<ul>
<li><strong>14-day right of withdrawal</strong> — You can cancel and return goods within 14 days of delivery, without giving any reason.</li>
<li><strong>Pre-contractual information</strong> — The trader must provide clear information about the product, total price, delivery costs, and the trader's identity before purchase.</li>
<li><strong>Delivery</strong> — Unless otherwise agreed, goods must be delivered within 30 days.</li>
<li><strong>Risk of loss</strong> — The risk passes to the consumer only when they (or a designated third party) physically take delivery.</li>
</ul>
<h3>Exceptions to Withdrawal</h3>
<p>Some products are excluded: sealed goods opened after delivery (hygiene/health), personalised items, perishable goods, digital content if performance has begun with consent.</p>""",
    pillar="consumer",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Directive 2011/83/EU (Consumer Rights Directive)",
    topic_tags=["online shopping", "distance selling", "withdrawal", "e-commerce"],
    url="https://mccaa.org.mt/Section/Content?contentId=1267",
)

add(
    title="Unfair Commercial Practices",
    content="""<h3>Banned Commercial Practices</h3>
<p>The <strong>Unfair Commercial Practices Directive</strong> protects consumers against dishonest business behaviour. A practice is unfair if it is contrary to professional diligence and materially distorts the consumer's decision-making.</p>
<h3>Types</h3>
<ul>
<li><strong>Misleading actions</strong> — False or deceptive information about a product</li>
<li><strong>Misleading omissions</strong> — Hiding or providing unclear crucial information</li>
<li><strong>Aggressive practices</strong> — Harassment, coercion, or undue influence</li>
</ul>
<h3>Blacklisted Practices</h3>
<p>31 practices are always considered unfair, including: bait advertising, fake "free" offers, persistent unwanted calls, claiming to be a signatory to a code of conduct when not, and pyramid schemes.</p>""",
    pillar="consumer",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Directive 2005/29/EC (UCPD)",
    topic_tags=["unfair practices", "misleading", "aggressive", "advertising"],
    url="https://mccaa.org.mt/Section/Content?contentId=1267",
)

add(
    title="Price Indication Requirements",
    content="""<h3>Displaying Prices</h3>
<p>All traders must indicate the <strong>selling price</strong> and <strong>unit price</strong> of products offered to consumers clearly, unambiguously, and in a manner easily identifiable.</p>
<h3>Rules</h3>
<ul>
<li>Prices must include VAT and all applicable taxes</li>
<li>The unit price (price per kilogram, litre, metre, etc.) must be displayed for pre-packaged goods</li>
<li>Any price reduction must show the prior price (the lowest price in the last 30 days before the reduction)</li>
</ul>
<h3>Enforcement</h3>
<p>The MCCAA regularly inspects retailers and online sellers for compliance. Infringements may result in administrative fines.</p>""",
    pillar="consumer",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Directive 98/6/EC, Consumer Affairs Act (Cap. 378)",
    topic_tags=["price indication", "unit price", "pricing", "discounts"],
    url="https://mccaa.org.mt/Section/Content?contentId=1267",
)


# ═══════════════════════════════════════════════════════════════
# STANDARDISATION
# ═══════════════════════════════════════════════════════════════

add(
    title="National Standards Body — MCCAA SMI",
    content="""<h3>Standards and Metrology Institute (SMI)</h3>
<p>The SMI, a division of the MCCAA, is Malta's <strong>National Standards Body (NSB)</strong> and <strong>National Metrology Institute (NMI)</strong>.</p>
<h3>Functions</h3>
<ul>
<li><strong>Standards development</strong> — Adopts European (CEN/CENELEC/ETSI) and international (ISO/IEC) standards as Maltese standards</li>
<li><strong>Standards information</strong> — Provides access to standards through the national standards catalogue</li>
<li><strong>National Enquiry Point</strong> — Under the TBT Agreement (WTO), handles notifications and enquiries about technical regulations and standards</li>
<li><strong>Metrology</strong> — Maintains national measurement standards and provides calibration and traceability services</li>
</ul>""",
    pillar="standardisation",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Standardisation Act (Cap. tried)",
    topic_tags=["SMI", "national standards", "metrology", "calibration"],
    url="https://mccaa.org.mt/Section/Content?contentId=1413",
)

add(
    title="Metrology & Calibration Services",
    content="""<h3>Legal and Industrial Metrology</h3>
<p>The MCCAA's SMI provides metrology services ensuring accurate and traceable measurements across Malta's economy.</p>
<h3>Services</h3>
<ul>
<li><strong>Calibration</strong> — Mass, volume, length, temperature, pressure, and electrical quantities</li>
<li><strong>Verification</strong> — Legal verification of measuring instruments used in trade (e.g., scales, fuel dispensers, taximeters)</li>
<li><strong>Pre-packaging controls</strong> — Verification that pre-packaged goods contain the correct quantity</li>
</ul>
<h3>Legal Framework</h3>
<p>Measuring instruments in Malta must comply with the <strong>Measuring Instruments Directive (MID)</strong> and the <strong>Non-Automatic Weighing Instruments Directive (NAWID)</strong>.</p>""",
    pillar="standardisation",
    scope="sector-specific",
    roles=["all"],
    legal_basis="Directive 2014/32/EU (MID), Directive 2014/31/EU (NAWID)",
    topic_tags=["metrology", "calibration", "verification", "measurement"],
    url="https://mccaa.org.mt/Section/Content?contentId=1413",
)


# ═══════════════════════════════════════════════════════════════
# GENERATE SQL OUTPUT
# ═══════════════════════════════════════════════════════════════

def escape_sql(s):
    """Escape single quotes for SQL."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

def pg_array(lst):
    """Format a Python list as a PostgreSQL array literal."""
    if not lst:
        return "'{}'::text[]"
    escaped = [str(x).replace("'", "''") for x in lst]
    return "'{" + ",".join(f'"{x}"' for x in escaped) + "}'::text[]"


print("-- MCCAA Knowledge Base Seed Data")
print(f"-- Total documents: {len(DOCUMENTS)}")
print("-- Generated by seed_kb.py\n")
print("BEGIN;\n")

# Clear existing seeded data (keep scraped data)
print("-- Remove previously seeded content (keep scraped website data)")
print("DELETE FROM documents WHERE slug IS NOT NULL;\n")

for doc in DOCUMENTS:
    sql = f"""INSERT INTO documents (title, content, url, type, sector, pillar, roles, topic_tags, scope, slug, legal_basis)
VALUES (
    {escape_sql(doc['title'])},
    {escape_sql(doc['content'])},
    {escape_sql(doc['url'])},
    'kb',
    {escape_sql(doc['sector'])},
    {escape_sql(doc['pillar'])},
    {pg_array(doc['roles'])},
    {pg_array(doc['topic_tags'])},
    {escape_sql(doc['scope'])},
    {escape_sql(doc['slug'])},
    {escape_sql(doc['legal_basis'])}
);"""
    print(sql)
    print()

print("COMMIT;")
print(f"\n-- Done. {len(DOCUMENTS)} documents inserted.")

