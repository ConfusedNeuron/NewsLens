"""Seed demo cards so the frontend has data immediately."""
import uuid
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import fetchone, get_conn

logger = logging.getLogger(__name__)

DEMO_CARDS = [
    {
        "headline": "RBI Holds Repo Rate at 6.5% for Sixth Consecutive Meeting",
        "summary_60w": "The Reserve Bank of India's Monetary Policy Committee unanimously held the benchmark repo rate at 6.5%, citing persistent food inflation and external uncertainties. The decision was widely expected but signals a prolonged pause before any easing cycle. Real rates remain positive at ~2%, giving RBI limited room to cut without triggering currency depreciation.",
        "what_happened": "RBI MPC held repo rate at 6.5% in its bi-monthly review.",
        "key_number": "6.5% repo rate — unchanged for 6th meeting",
        "winners_json": json.dumps([
            {"who": "Existing home loan borrowers on fixed EMIs", "why": "No increase in monthly payments", "magnitude": "~9 crore home loan accounts unaffected"},
            {"who": "Banking sector NIM stability", "why": "Spreads remain predictable", "magnitude": "Nifty Bank flat to +0.3%"}
        ]),
        "losers_json": json.dumps([
            {"who": "New home buyers", "why": "High EMIs persist — no relief from rate cut", "magnitude": "30-year loan on ₹50L costs ~₹43,000/month vs ₹36,000 pre-hike cycle"},
            {"who": "Fixed deposit savers", "why": "Opportunity cost — rates not rising further", "magnitude": "~0.3% annualized opportunity cost vs peak FD rates"}
        ]),
        "india_angle": "The RBI's pause is India-specific — food inflation driven by uneven monsoon is the primary constraint. Core inflation has moderated to 4.1%, but vegetable prices remain volatile. FII equity flows remain positive at $2.3B this month, supporting the rupee above 83.5.",
        "usa_angle": "Fed policy divergence is widening — the Fed is also holding rates but inflation trajectory in the US is different. Dollar strength (DXY 104.2) limits RBI's ability to cut without INR weakness.",
        "china_angle": "PBOC has been easing while RBI holds — creating capital flow dynamics where Indian bonds look relatively attractive to EM investors, supporting FII debt flows.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance"]),
        "geo_tags": json.dumps(["India", "Global"]),
        "confidence_badge": "high",
        "source_name": "Economic Times",
        "source_url": "https://economictimes.indiatimes.com",
    },
    {
        "headline": "OpenAI Launches GPT-5 with Native Multimodal Reasoning — Anthropic, Google Under Pressure",
        "summary_60w": "OpenAI released GPT-5, claiming 40% improvement on reasoning benchmarks over GPT-4o. The model handles text, images, audio, and video natively in a unified context window. Enterprise pricing starts at $60 per million tokens. Anthropic's Claude and Google's Gemini face immediate competitive pressure as enterprise customers begin evaluating switching costs.",
        "what_happened": "OpenAI launched GPT-5 with native multimodal capabilities and significantly improved reasoning.",
        "key_number": "40% improvement on MMLU reasoning — 92.3% vs GPT-4o's 65.9%",
        "winners_json": json.dumps([
            {"who": "Enterprise software developers", "why": "More capable models reduce engineering complexity for AI products", "magnitude": "~4.2M OpenAI API users gain access immediately"},
            {"who": "OpenAI (Microsoft MSFT +2.1%)", "why": "First-mover advantage in GPT-5 cycle; enterprise contracts likely to lock in", "magnitude": "Microsoft's AI revenue segment estimated +$800M annualized uplift"}
        ]),
        "losers_json": json.dumps([
            {"who": "Anthropic (Claude) and Google (Gemini)", "why": "Benchmark gap widens; enterprise evaluation cycles favor OpenAI", "magnitude": "Alphabet (GOOGL -1.3%) on the news; market cap impact ~$22B"},
            {"who": "AI application companies with single-model dependency", "why": "Must re-evaluate architecture — switching costs ~3-6 months engineering time", "magnitude": "Estimated 15-20% of AI startups using GPT-4 exclusively"}
        ]),
        "india_angle": "India's IT sector (TCS, Infosys, Wipro) faces dual pressure: clients will demand AI-powered services faster, while internal automation may reduce headcount requirements. TCS AI revenue share is 8% and rising. Bengaluru-based AI startups gain access to better foundational models without cost increase.",
        "usa_angle": "Microsoft's $13B investment in OpenAI looks prescient. Azure's AI services are the primary distribution channel for GPT-5. AWS and GCP face increased competitive pressure in cloud AI workloads.",
        "china_angle": "Chinese AI firms (Baidu ERNIE, Alibaba Qwen) face a wider capability gap. Export controls limit their access to advanced NVIDIA GPUs needed to train comparable models. Tech sovereignty concerns intensify.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Tech"]),
        "geo_tags": json.dumps(["USA", "Global", "India"]),
        "confidence_badge": "high",
        "source_name": "TechCrunch",
        "source_url": "https://techcrunch.com",
    },
    {
        "headline": "India-China Border Trade Agreement — First Bilateral Deal in 5 Years",
        "summary_60w": "India and China signed a framework border trade agreement covering Himalayan border trade posts and visa easing for business travelers after a 5-year freeze following the 2020 Galwan clash. Trade between the two countries has continued despite political tension — bilateral trade was $136B in 2024 — but the formal agreement signals a diplomatic thaw ahead of SCO summit.",
        "what_happened": "India and China signed a border trade framework agreement after a 5-year diplomatic freeze.",
        "key_number": "$136B India-China bilateral trade in 2024 — set to rise with formal agreement",
        "winners_json": json.dumps([
            {"who": "Indian importers of Chinese electronics and machinery", "why": "Formal channels reduce risk premium and customs friction", "magnitude": "~$42B electronics imports annually — 5-10% friction cost reduction estimated"},
            {"who": "Indian pharma and textile exporters", "why": "China market access improves for key export sectors", "magnitude": "India exports $4.1B to China — formal agreement may add 15-20%"}
        ]),
        "losers_json": json.dumps([
            {"who": "Indian domestic electronics manufacturers", "why": "Cheaper Chinese goods may undercut Make in India PLI scheme beneficiaries", "magnitude": "PLI electronics scheme — ₹41,000 Cr committed; margin pressure on assembled goods"},
            {"who": "India's 'China+1' narrative in FDI pitches", "why": "Warmer relations reduce urgency for global manufacturers to diversify away from China", "magnitude": "FDI pipeline at risk — ~$8B in announced but uncommitted manufacturing investments"}
        ]),
        "india_angle": "The agreement is strategically significant — it signals that India is separating economic pragmatism from military posturing. The rupee strengthened 0.2% on the news. Indian border state economies (Himachal, Uttarakhand, Sikkim) benefit from formal trade routes.",
        "usa_angle": "Washington will monitor this closely — India-China rapprochement complicates the QUAD alliance narrative. The US may accelerate bilateral trade deal discussions with India to retain strategic alignment.",
        "china_angle": "Beijing gains a diplomatic win heading into SCO presidency. The agreement helps China signal that economic statecraft can overcome geopolitical friction — a message aimed at ASEAN and African nations.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Geopolitics", "Finance"]),
        "geo_tags": json.dumps(["India", "China", "Global"]),
        "confidence_badge": "high",
        "source_name": "The Hindu",
        "source_url": "https://thehindu.com",
    },
    {
        "headline": "India Surpasses 2030 Solar Target 7 Years Early — 200GW Installed",
        "summary_60w": "India announced it has crossed 200 gigawatts of installed solar capacity, surpassing the original 2030 Paris Agreement target seven years ahead of schedule. The milestone was driven by aggressive Rajasthan and Gujarat utility-scale projects and rooftop solar subsidies. India is now the third-largest solar market globally after China and the EU.",
        "what_happened": "India reached 200GW solar installed capacity, 7 years before its 2030 Paris target.",
        "key_number": "200GW solar installed — #3 globally, 7 years ahead of 2030 target",
        "winners_json": json.dumps([
            {"who": "Indian renewable energy companies (Adani Green, Tata Power Renewable)", "why": "Early milestone boosts green bond access and international capital", "magnitude": "Adani Green AGEL +4.2%; sector-wide market cap gain ~₹28,000 Cr"},
            {"who": "Rural electricity consumers in Rajasthan, Gujarat, MP", "why": "Expanded solar grid reduces load shedding and subsidized tariffs", "magnitude": "~85 million households in solar-heavy states benefit from tariff stability"}
        ]),
        "losers_json": json.dumps([
            {"who": "Coal plant operators and Coal India", "why": "Energy transition accelerates plant retirement timelines", "magnitude": "Coal India (COALINDIA.NS -1.8%); 12 plants with 9.4GW capacity under accelerated retirement review"},
            {"who": "Chinese solar panel manufacturers", "why": "India's domestic manufacturing push (BCD tariff) shifts procurement", "magnitude": "Basic customs duty of 40% on solar cells has reduced Chinese panel imports by ~35%"}
        ]),
        "india_angle": "This is a significant credibility boost for India's climate commitments ahead of COP31. The renewable energy sector has attracted $9.4B FDI this year. Green hydrogen ambitions (5MT by 2030) now look more achievable with cheap solar power as feedstock.",
        "usa_angle": "US clean energy manufacturers (First Solar) and developers view India as a major export market. The IRA's domestic content provisions compete with India for clean energy FDI — but India's labour cost advantage remains.",
        "china_angle": "China dominates 85% of global solar panel manufacturing. India's BCD tariff is directly aimed at reducing Chinese dependency. Chinese Tier-1 manufacturers are exploring India JV manufacturing to circumvent the tariff.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Environment", "Finance"]),
        "geo_tags": json.dumps(["India", "Global"]),
        "confidence_badge": "high",
        "source_name": "Down To Earth",
        "source_url": "https://downtoearth.org.in",
    },
    {
        "headline": "Fed Signals Two Rate Cuts in 2026 — Equity Markets Rally",
        "summary_60w": "Federal Reserve Chair signaled two 25-basis-point rate cuts are likely in 2026 if inflation continues its downward trend, with the first expected in Q2. US CPI has moderated to 2.8%. S&P 500 gained 1.4% on the news, with rate-sensitive sectors leading. Emerging markets including India saw FII inflows surge as dollar weakening expectations took hold.",
        "what_happened": "Fed signaled two rate cuts in 2026, triggering a global equity rally and EM capital inflows.",
        "key_number": "2 x 25bps Fed cuts expected 2026 — S&P +1.4% on announcement",
        "winners_json": json.dumps([
            {"who": "Indian equity markets and FII inflows", "why": "Weaker dollar and lower US rates push capital toward EM; India premium", "magnitude": "Nifty 50 +1.1%; FII net buy ₹4,200 Cr on the day"},
            {"who": "US growth stocks and tech sector", "why": "Lower discount rates boost DCF valuations for long-duration assets", "magnitude": "NASDAQ +2.1%; estimated $380B market cap added across Mag-7"}
        ]),
        "losers_json": json.dumps([
            {"who": "US dollar (DXY index)", "why": "Rate cut expectations reduce yield differential vs EUR/JPY/INR", "magnitude": "DXY fell to 101.8 from 104.2 — INR strengthened to 82.9 from 83.5"},
            {"who": "USD-denominated cash holders and money market funds", "why": "Lower future yields reduce return on short-duration dollar assets", "magnitude": "$6.3T in US money market funds face lower forward returns"}
        ]),
        "india_angle": "INR appreciation to 82.9 is a double-edged sword — it helps importers (crude oil bill drops ~$2B annualized at current import volumes) but hurts IT exporters like Infosys, TCS whose USD revenues get translated at lower rates. Every 1 rupee of INR appreciation costs Indian IT sector ~1.5% in revenue.",
        "usa_angle": "The Fed's pivot reflects confidence in disinflation — but the risk is premature easing reigniting inflation. Fed Funds Futures now price 54% probability of June cut. Treasury 10Y yield fell to 4.21%.",
        "china_angle": "Yuan appreciated against dollar on the news (USD/CNY 7.18 from 7.24). China's PBOC has more room to ease now without triggering capital outflows — this may accelerate PBOC's own easing timeline.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance"]),
        "geo_tags": json.dumps(["USA", "India", "Global"]),
        "confidence_badge": "high",
        "source_name": "Reuters Business",
        "source_url": "https://reuters.com",
    },
    {
        "headline": "Nvidia Unveils Blackwell Ultra — 4x Performance Gain Over H100 at Same Price",
        "summary_60w": "Nvidia announced Blackwell Ultra GPUs delivering 4x AI training throughput versus H100 at equivalent data center pricing. The chip uses 3nm TSMC process and 192GB HBM3e memory. Cloud providers AWS, Azure, GCP announced day-one availability. Competitors AMD and Intel saw stock declines as the performance gap widens further in Nvidia's favor.",
        "what_happened": "Nvidia launched Blackwell Ultra GPUs with 4x AI performance over H100 at the same price point.",
        "key_number": "4x AI training throughput vs H100 — same datacenter pricing",
        "winners_json": json.dumps([
            {"who": "Nvidia (NVDA)", "why": "Dominant position reinforced; switching costs for cloud providers remain extremely high", "magnitude": "NVDA +5.8% — market cap increased ~$155B; AI revenue guidance raised by 18%"},
            {"who": "TSMC (TSM)", "why": "Sole 3nm manufacturer for Blackwell Ultra; supply is the bottleneck", "magnitude": "TSM +3.1%; CoWoS packaging capacity sold out through Q2 2027"}
        ]),
        "losers_json": json.dumps([
            {"who": "AMD (INSTINCT MI300X) and Intel (Gaudi 3)", "why": "Performance gap widens further; enterprise evaluations will default to Nvidia", "magnitude": "AMD -4.1% ($8.2B market cap loss); Intel -2.3% on the day"},
            {"who": "Chinese AI companies facing export controls", "why": "Cannot access Blackwell Ultra due to US BIS export restrictions; stuck on H100 equivalents", "magnitude": "Chinese AI training cost disadvantage estimated at 3-4x vs US peers going forward"}
        ]),
        "india_angle": "Indian cloud companies (Yotta, CtrlS) and hyperscalers must wait for allocation — India's GPU access is constrained. However, Indian AI startups on Azure/AWS get immediate access. Infosys and Wipro's AI practices benefit from offering clients faster model training.",
        "usa_angle": "Nvidia's data center revenue is now 85% of total revenue at $47B quarterly run rate. Jensen Huang confirmed US domestic manufacturing plans — new fab in Arizona tied to CHIPS Act funding.",
        "china_angle": "Export restrictions mean Chinese companies receive H100-equivalent Nvidia H20 chips, now two generations behind. Huawei Ascend 910C is the domestic alternative — but only 40% of H100 performance at 2x the price.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Tech"]),
        "geo_tags": json.dumps(["USA", "China", "Global"]),
        "confidence_badge": "high",
        "source_name": "TechCrunch",
        "source_url": "https://techcrunch.com",
    },
    {
        "headline": "Brent Crude Drops to $72 — OPEC+ Output Increase Overwhelms Demand",
        "summary_60w": "Brent crude fell to $72 per barrel after OPEC+ confirmed a 500,000 barrel per day production increase starting next month, citing improving member fiscal positions. Global demand growth estimates for 2026 were revised down 0.3% by the IEA. India, the world's third-largest oil importer, stands to benefit significantly from every dollar fall in crude prices.",
        "what_happened": "OPEC+ increased output by 500,000 bpd, sending Brent crude to $72 — a 14-month low.",
        "key_number": "$72/barrel Brent — 14-month low, down from $85 in January",
        "winners_json": json.dumps([
            {"who": "India's current account and fiscal deficit", "why": "India imports 85% of its crude — lower prices cut import bill substantially", "magnitude": "Every $10 fall in crude saves India ~$14B annually — this $13 fall saves ~$18B/year"},
            {"who": "Indian consumers and transport sector", "why": "Petrol and diesel prices likely to be cut by ₹3-5/litre in the next fuel revision", "magnitude": "~23 crore two-wheelers and 3.2 crore cars benefit from lower fuel costs"}
        ]),
        "losers_json": json.dumps([
            {"who": "Oil exporting nations (Saudi Arabia, UAE, Russia)", "why": "Budget breakeven for Saudi Arabia is $81/barrel — current price is below that", "magnitude": "Saudi Arabia faces ~$25B annual budget gap at $72 vs $85 planning assumption"},
            {"who": "Indian oil marketing companies (HPCL, BPCL, IOC)", "why": "Inventory losses on high-price crude already purchased before the price fall", "magnitude": "HPCL -3.2%, BPCL -2.8% as inventory loss estimates circulate"}
        ]),
        "india_angle": "The oil price drop is unambiguously positive for India's macro — current account deficit narrows, inflation moderates, and there's fiscal room for a fuel price cut before elections. RBI's inflation forecast may be revised down, opening the door for rate cuts sooner than expected.",
        "usa_angle": "US shale producers (WTI at $68) face margin pressure but can be profitable at $55+. US energy sector stocks (XLE -2.1%) fall on price weakness but domestic consumption demand remains strong.",
        "china_angle": "China is the world's largest oil importer ($380B/year) — lower crude is unambiguously positive for China's trade balance and domestic fuel subsidies. Petrochemical margins improve.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance", "Environment"]),
        "geo_tags": json.dumps(["India", "Global"]),
        "confidence_badge": "high",
        "source_name": "Reuters Business",
        "source_url": "https://reuters.com",
    },
    {
        "headline": "Apple Launches iPhone 17 with On-Device AI — No Subscription Required",
        "summary_60w": "Apple announced iPhone 17 with an upgraded A19 chip enabling full on-device AI features including real-time translation, advanced Siri reasoning, and photo editing — all without cloud subscription. The move directly counters Google's Gemini and OpenAI's subscription models. Pre-orders exceeded 5 million in 24 hours globally.",
        "what_happened": "Apple launched iPhone 17 with comprehensive on-device AI — no cloud subscription or extra fee.",
        "key_number": "5M pre-orders in 24 hours — estimated $4.5B first-weekend revenue",
        "winners_json": json.dumps([
            {"who": "Apple (AAPL) and TSMC", "why": "Premium pricing power maintained; A19 chip demand drives TSMC N3P revenue", "magnitude": "AAPL +3.4%; iPhone 17 ASP estimated at $1,150 vs iPhone 16 $1,099 — +5% premium"},
            {"who": "Consumers with privacy concerns about cloud AI", "why": "On-device processing means personal data never leaves the device", "magnitude": "Privacy-first positioning appeals to ~35% of users who disabled Siri cloud features in surveys"}
        ]),
        "losers_json": json.dumps([
            {"who": "Google (Gemini subscription) and OpenAI (ChatGPT Plus)", "why": "Apple's free on-device AI undercuts the $20/month subscription argument for mobile users", "magnitude": "Google down 1.8% ($36B market cap); ChatGPT mobile subscription growth may slow"},
            {"who": "Samsung and Android OEMs", "why": "Apple's on-device AI differentiation widens the premium smartphone moat", "magnitude": "Samsung Galaxy S25 Ultra loses a key differentiating feature — Qualcomm-based on-device AI is behind Apple Silicon"}
        ]),
        "india_angle": "India is Apple's fastest-growing market (+38% YoY). iPhone 17 manufactured in India (Tata Electronics, Foxconn India) for the first time at launch — reduces import duty and supports Make in India. Domestic IT channel partners benefit from higher volumes.",
        "usa_angle": "Apple's on-device AI strategy is a direct response to EU data sovereignty requirements and a hedge against any regulatory action on cloud data processing. Stock buyback of $90B announced alongside the launch.",
        "china_angle": "Apple's China sales remain under pressure from Huawei Mate resurgence — iPhone 17 launch in China was delayed by 2 weeks for regulatory approvals. Foxconn China shifts further production capacity to India.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Tech"]),
        "geo_tags": json.dumps(["USA", "India", "China"]),
        "confidence_badge": "high",
        "source_name": "TechCrunch",
        "source_url": "https://techcrunch.com",
    },
    {
        "headline": "Monsoon Deficit 18% Below Normal — Kharif Crop Output at Risk",
        "summary_60w": "India's southwest monsoon is tracking 18% below the long-period average through mid-season, with severe deficits in Marathwada, Vidarbha, and parts of Rajasthan. The IMD has not issued an official drought warning yet, but agriculture economists estimate kharif output — particularly pulses and coarse grains — may fall 8-12% if the deficit persists through August.",
        "what_happened": "India's 2026 southwest monsoon is 18% below normal, threatening kharif crop output.",
        "key_number": "18% below normal monsoon — kharif output risk of -8 to -12%",
        "winners_json": json.dumps([
            {"who": "Agricultural commodity traders and dal/pulses importers", "why": "Supply shortfall drives domestic prices up — import arbitrage becomes profitable", "magnitude": "Tur dal prices already up 22% YoY; imports from Myanmar and Australia likely to rise"},
            {"who": "Irrigation equipment companies (Jain Irrigation, EPC Industries)", "why": "Drip irrigation and micro-irrigation demand spikes in deficit areas", "magnitude": "Jain Irrigation JISLJALEQS +6.1% on week"}
        ]),
        "losers_json": json.dumps([
            {"who": "Kharif crop farmers in Maharashtra, Rajasthan, and MP", "why": "Crop losses directly reduce farmer income in already-stressed regions", "magnitude": "~4.2 crore farm households in deficit regions; average income impact ₹18,000-45,000"},
            {"who": "Rural consumption and FMCG companies", "why": "Agricultural income drop reduces rural purchasing power", "magnitude": "Rural FMCG volume growth may slow from +8% to +4-5% in H2 FY27"}
        ]),
        "india_angle": "This is the most directly India-specific story this week. Food inflation — already elevated at 7.2% — will likely spike further. RBI's rate cut timeline is now under threat. The government may need to release buffer stocks of pulses and allow increased imports, putting pressure on domestic farmers.",
        "usa_angle": "US soybean and wheat futures rise on potential increased Indian import demand. USDA export forecasts for India may be revised upward.",
        "china_angle": "China is a major pulse exporter — Indian government may fast-track import approvals from China as a diplomatic and supply move.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Environment", "Finance"]),
        "geo_tags": json.dumps(["India"]),
        "confidence_badge": "high",
        "source_name": "Down To Earth",
        "source_url": "https://downtoearth.org.in",
    },
    {
        "headline": "Infosys Raises FY27 Revenue Guidance to 8-10% — AI-Led Deal Pipeline at Record High",
        "summary_60w": "Infosys raised its full-year revenue growth guidance to 8-10% in constant currency after a strong Q1, citing AI-led transformation deals and cost optimization mandates from BFSI and retail clients. Large deal wins hit $5.2B in Q1 — an all-time quarterly record. The company added 12,000 AI-skilled employees in the quarter.",
        "what_happened": "Infosys raised FY27 guidance to 8-10% CC growth with record Q1 large deal wins of $5.2B.",
        "key_number": "$5.2B large deal TCV in Q1 FY27 — all-time quarterly record",
        "winners_json": json.dumps([
            {"who": "Infosys shareholders", "why": "Guidance upgrade signals acceleration from 4-6% last year; re-rating likely", "magnitude": "INFY +8.4% on earnings day; ADR hit 52-week high at $23.40"},
            {"who": "Infosys employees with ESOPs and skill premiums for AI", "why": "Company is hiring and paying premiums for AI/ML skills amid record revenue", "magnitude": "AI skill premium estimated at 18-22% over base salary for new hires"}
        ]),
        "losers_json": json.dumps([
            {"who": "TCS and Wipro (competitive positioning)", "why": "Infosys outperforming on deal wins raises expectations for peers; TCS guidance unchanged", "magnitude": "TCS marginally underperformed Infosys by 340bps on earnings day"},
            {"who": "Indian IT mid-caps (Mphasis, L&T Tech, Persistent)", "why": "Large deal winners tend to be tier-1; mid-caps may see deal flow diverted to Infosys-sized bids", "magnitude": "Mid-cap IT index -1.2% as Infosys takes dominant narrative share"}
        ]),
        "india_angle": "Infosys represents India's IT sector bellwether — the guidance upgrade is read as a positive signal for the entire $250B IT export industry. Bengaluru commercial real estate and talent market will feel positive effects. Nifty IT index gained 2.8% on the week.",
        "usa_angle": "US BFSI and retail clients are the primary deal sources — this signals that US enterprises are spending on AI transformation despite macro uncertainty. AI capex cycles are clearly underway.",
        "china_angle": "Infosys has minimal China exposure — China's preference for domestic IT vendors (Alibaba Cloud, Huawei) means Indian IT is not competing there.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance", "Tech"]),
        "geo_tags": json.dumps(["India", "USA", "Global"]),
        "confidence_badge": "high",
        "source_name": "Economic Times",
        "source_url": "https://economictimes.indiatimes.com",
    },
    {
        "headline": "China Launches $300B Infrastructure Stimulus — Focus on Rural Roads and EV Charging",
        "summary_60w": "China's State Council approved a ¥2.1 trillion ($300B) infrastructure stimulus package targeting rural road construction, EV charging network expansion to 300 cities, and water management in drought-prone provinces. The move signals Beijing's shift from export-led to domestic consumption-driven growth, with local government bond issuance covering 60% of the financing.",
        "what_happened": "China approved a $300B infrastructure stimulus focused on rural connectivity and EV charging networks.",
        "key_number": "¥2.1 trillion ($300B) stimulus — 1.4% of China's GDP",
        "winners_json": json.dumps([
            {"who": "Chinese EV manufacturers (BYD, CATL, NIO)", "why": "300-city charging network removes range anxiety — accelerates EV adoption in tier-2/3 cities", "magnitude": "BYD +4.2%; EV penetration target raised to 50% of new car sales by 2027"},
            {"who": "Steel, cement, and construction material producers", "why": "Rural road construction creates immediate demand for raw materials", "magnitude": "China steel futures +2.8%; estimated 45M tons additional steel demand over 3-year project"}
        ]),
        "losers_json": json.dumps([
            {"who": "China's fiscal position and local government debt", "why": "60% local government bond financing raises already elevated LG debt concerns", "magnitude": "Local government debt/GDP ratio rises from 35% to estimated 38% by project completion"},
            {"who": "Petrol vehicle manufacturers and fuel retailers", "why": "EV charging network build-out accelerates ICE vehicle displacement in rural China", "magnitude": "China gasoline consumption growth forecast cut to +1.2% from +3.8% by IEA"}
        ]),
        "india_angle": "China stimulus is mixed for India — positive for commodity exporters (iron ore, specialty chemicals) but Chinese infrastructure build increases competition for global steel markets. Indian steel stocks (JSW, Tata Steel) fell on fear of Chinese dumping risk.",
        "usa_angle": "The stimulus signals China is managing its property sector downturn via infrastructure — reducing the risk of a hard landing that would have global contagion effects. US Treasury sees it as sustainable demand management.",
        "china_angle": "This is Beijing's largest domestic consumption stimulus since 2015. The EV focus reflects China's strategic bet on becoming the dominant EV exporter — by building domestic adoption first, they drive down costs for export.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance", "Geopolitics"]),
        "geo_tags": json.dumps(["China", "Global"]),
        "confidence_badge": "high",
        "source_name": "South China Morning Post",
        "source_url": "https://scmp.com",
    },
    {
        "headline": "EU Passes AI Act Phase 2 — High-Risk AI Must Be Audited, Fined Up to 3% Global Revenue",
        "summary_60w": "The European Union's AI Act Phase 2 implementation kicked in, requiring operators of high-risk AI systems in hiring, credit scoring, and critical infrastructure to conduct conformity assessments and register with national authorities. Fines for non-compliance reach 3% of global annual turnover. US tech companies with EU operations face the highest compliance burden.",
        "what_happened": "EU AI Act Phase 2 mandatory compliance began — high-risk AI must be audited or face 3% revenue fines.",
        "key_number": "3% of global annual revenue — maximum fine for high-risk AI non-compliance",
        "winners_json": json.dumps([
            {"who": "AI compliance and auditing firms (PwC, Deloitte, specialist AI auditors)", "why": "New mandatory audit requirements create immediate demand for AI risk assessment services", "magnitude": "EU AI compliance market estimated at €4.2B annually once fully implemented"},
            {"who": "European AI startups with GDPR/privacy-by-design culture", "why": "Compliance is already embedded in their product design — incumbency advantage over US hyperscalers", "magnitude": "EU-native AI companies may attract premium B2B pricing vs non-compliant alternatives"}
        ]),
        "losers_json": json.dumps([
            {"who": "US tech companies (Google, Microsoft, Meta, OpenAI) with EU operations", "why": "Compliance cost estimated at $180-400M per company; feature limitations in EU market", "magnitude": "Alphabet estimated €1.8B in EU AI compliance costs; Meta has already restricted some Llama features in EU"},
            {"who": "EU businesses using AI in hiring and credit decisions", "why": "Must audit existing systems and update workflows — significant one-time and ongoing cost", "magnitude": "EU banking sector alone: estimated €800M compliance cost in Year 1"}
        ]),
        "india_angle": "Indian IT companies with EU clients (Infosys, TCS, Wipro) see new revenue opportunity — EU clients will outsource AI compliance and auditing work to Indian service providers. India is also watching closely to draft its own AI regulation framework.",
        "usa_angle": "US companies are lobbying aggressively against extraterritorial application. The Biden/Trump administrations have resisted a US federal AI Act — EU regulation creates a de facto global standard due to market size.",
        "china_angle": "Chinese AI companies have minimal EU exposure due to data sovereignty restrictions. The EU Act actually helps China's domestic AI ecosystem by limiting the competitiveness of US-based global AI platforms.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Tech", "Geopolitics"]),
        "geo_tags": json.dumps(["Global", "USA"]),
        "confidence_badge": "medium",
        "source_name": "BBC World News",
        "source_url": "https://bbc.co.uk",
    },
    {
        "headline": "Nifty 50 Crosses 27,000 — FII Buying Streak Longest Since 2020",
        "summary_json": "Nifty 50 crossed 27,000 for the first time on sustained FII buying totaling ₹42,000 crore over 18 consecutive sessions — the longest buying streak since the post-COVID recovery of late 2020. Domestic mutual fund flows remain positive at ₹18,000 crore SIP inflows per month. Midcap and smallcap indices outperformed, gaining 3.2% and 4.1% respectively on the week.",
        "what_happened": "Nifty 50 crossed 27,000 driven by 18-day FII buying streak totaling ₹42,000 crore.",
        "key_number": "27,000 Nifty — 18 consecutive FII buying sessions, ₹42,000 Cr inflows",
        "winners_json": json.dumps([
            {"who": "Equity mutual fund investors and SIP participants", "why": "Portfolio NAVs rise; long-term SIP investors at higher mark-to-market returns", "magnitude": "~8.3 crore SIP folios gain; AMFI estimates ₹2.2 lakh crore in SIP AUM appreciated"},
            {"who": "Banking and financial sector (Nifty Bank +2.9%)", "why": "FII preference for large-cap financials drives banking stocks; HDFC Bank, ICICI lead", "magnitude": "HDFC Bank +4.1%; ICICI +3.6% on the month"}
        ]),
        "losers_json": json.dumps([
            {"who": "Recent IPO investors and new retail entrants at high valuations", "why": "Market at 22x forward P/E — entering at peak creates valuation risk", "magnitude": "Nifty 50 P/E of 22x vs 10-year average of 19x — 15% premium to historical mean"},
            {"who": "Exporters facing INR appreciation", "why": "Strong capital inflows push rupee to 82.8 — reducing INR value of dollar revenues", "magnitude": "IT sector revenue impact: ~1.5% per rupee appreciation — estimated 1.2% headwind this quarter"}
        ]),
        "india_angle": "The 27,000 milestone is driven by genuine fundamental improvement — GST collections at record ₹2.1 lakh crore, corporate earnings growth at 15% YoY, and a stable macro backdrop. This is not purely liquidity-driven; domestic investors have provided consistent support via SIPs.",
        "usa_angle": "US rate cut expectations are a tailwind — EM equity allocations increase when US rates fall. India has received the largest share of EM FII flows in Asia ex-China this year.",
        "china_angle": "China's weak stock market (Shanghai Composite -3% YTD) has diverted Asian EM allocations to India. The India-China FII flow divergence is at a 5-year high.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance"]),
        "geo_tags": json.dumps(["India", "Global"]),
        "confidence_badge": "high",
        "source_name": "Economic Times",
        "source_url": "https://economictimes.indiatimes.com",
    },
    {
        "headline": "Arctic Sea Ice Hits Record Low — 23% Below 1980s Average",
        "summary_60w": "Arctic sea ice extent in May 2026 is tracking 23% below the 1980-2010 average — the lowest on satellite record for this time of year. Climate scientists link the decline to a rapid Arctic amplification effect where the polar region is warming 4x faster than the global average. Implications include accelerated permafrost melt, methane release, and disruption of the polar vortex.",
        "what_happened": "Arctic sea ice hit a record low in May 2026 — 23% below the 1980s baseline.",
        "key_number": "23% below 1980s average — lowest Arctic ice extent on satellite record",
        "winners_json": json.dumps([
            {"who": "Arctic shipping companies and Northern Sea Route operators", "why": "Reduced ice enables year-round commercial shipping through Arctic — cuts Europe-Asia route by 30%", "magnitude": "Northern Sea Route transit time: 12 days vs 20+ via Suez Canal — est. $500M annual freight savings if scalable"},
            {"who": "Greenland resource extraction companies", "why": "Permafrost melt exposes rare earth and mineral deposits previously inaccessible", "magnitude": "Greenland has est. 38 of 50 critical minerals — potential $1T+ in resources becoming accessible"}
        ]),
        "losers_json": json.dumps([
            {"who": "Coastal communities in Bangladesh, Vietnam, Indonesia", "why": "Accelerated ice melt contributes to sea level rise — these nations have highest exposure", "magnitude": "1.5m sea level rise scenario: 17 million Bangladeshis permanently displaced; est. $280B GDP at risk"},
            {"who": "Global insurance industry", "why": "Climate risk repricing affects property insurance in coastal and extreme weather zones globally", "magnitude": "Swiss Re estimates $500B+ annual uninsured climate losses by 2035 at current trajectory"}
        ]),
        "india_angle": "India's coastal cities — Mumbai, Chennai, Kolkata — face long-term sea level and storm surge risk. The monsoon system is increasingly disrupted by Arctic changes (polar vortex effects). India's ₹1 lakh crore climate adaptation fund will need to be scaled significantly.",
        "usa_angle": "Alaska faces direct impacts — permafrost infrastructure damage costs $5.5B in federal infrastructure at risk. Arctic opening creates geopolitical competition with Russia and China for shipping routes and resources.",
        "china_angle": "China has a major stake in Arctic routes and has Observer status in the Arctic Council. Northern Sea Route dramatically reduces China-Europe shipping time. Beijing has invested $90B in Arctic infrastructure through Belt & Road Arctic extension.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Environment"]),
        "geo_tags": json.dumps(["Global"]),
        "confidence_badge": "high",
        "source_name": "Carbon Brief",
        "source_url": "https://carbonbrief.org",
    },
    {
        "headline": "GST Collections Cross ₹2 Lakh Crore — Record High, Third Month Running",
        "summary_60w": "India's Goods and Services Tax collections crossed ₹2 lakh crore for the third consecutive month in April, reaching ₹2.13 lakh crore — a 13.4% YoY increase. The sustained record reflects improved compliance, economic activity, and e-invoicing enforcement. Finance ministry said no GST rate revision is planned this quarter.",
        "what_happened": "India GST collections hit ₹2.13 lakh crore in April — third consecutive month above ₹2L crore.",
        "key_number": "₹2.13 lakh crore GST — 13.4% YoY growth, 3rd consecutive record month",
        "winners_json": json.dumps([
            {"who": "Central and state governments (fiscal position)", "why": "Strong GST reduces dependence on market borrowing; fiscal consolidation ahead of target", "magnitude": "Centre's GST share: ₹1.06 lakh crore; states share balance — fiscal deficit narrows to 5.1% vs 5.6% budget"},
            {"who": "Bond market and government security investors", "why": "Better fiscal position reduces government borrowing — lower supply pushes yields down", "magnitude": "10-year G-Sec yield fell to 6.82% from 7.05% — 23bps rally"}
        ]),
        "losers_json": json.dumps([
            {"who": "Informal sector and cash-economy businesses", "why": "Improved GST compliance enforcement is reducing informal economy advantages", "magnitude": "Informal economy share of GDP estimated falling from 48% to 44% — compliance pressure on small traders"},
            {"who": "Tax consultants arguing for rate rationalization", "why": "Record collections remove the political urgency for rate cuts on common goods", "magnitude": "28% slab goods (ACs, luxury items) unlikely to be cut in near-term — consumer electronics lobby disappointed"}
        ]),
        "india_angle": "This is purely positive for India's macro narrative. Strong GST reduces RBI's concern about fiscal slippage, potentially allowing more coordination on rate policy. India's credit ratings outlook from Moody's and S&P may improve — positive for sovereign bond spreads and corporate borrowing costs.",
        "usa_angle": "Rating agency upgrades for India would make Indian government bonds more attractive to global fixed income funds — further supporting INR and FII debt flows.",
        "china_angle": "China's equivalent — VAT — has shown declining collections as economic activity slows. India's divergence in tax collection trajectory is increasingly cited in EM investment cases.",
        "personal_impact": "",
        "domain_tags": json.dumps(["Finance"]),
        "geo_tags": json.dumps(["India"]),
        "confidence_badge": "high",
        "source_name": "Economic Times",
        "source_url": "https://economictimes.indiatimes.com",
    },
]


def seed_demo_cards() -> int:
    """
    Insert the demo cards, flagged `is_seed = TRUE`.

    These stories are INVENTED. "Nifty 50 Crosses 27,000" never happened; it is
    illustrative copy for developing the UI without running the pipeline. Every row
    carries is_seed so the API can label them and so they can be removed in one
    statement (`DELETE FROM cards WHERE is_seed = TRUE`).
    """
    now = datetime.utcnow()
    with get_conn() as conn:
        for i, card in enumerate(DEMO_CARDS):
            card_id = str(uuid.uuid4())
            created_at = (now - timedelta(hours=i * 2)).isoformat()
            conn.execute(
                """INSERT OR IGNORE INTO cards
                   (id, headline, summary_60w, what_happened, key_number, winners_json, losers_json,
                    india_angle, usa_angle, china_angle, personal_impact, domain_tags, geo_tags,
                    confidence_badge, source_name, source_url, is_live, is_seed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, TRUE, ?)""",
                (
                    card_id,
                    card.get("headline", ""),
                    card.get("summary_60w") or card.get("summary_json", ""),
                    card.get("what_happened", ""),
                    card.get("key_number", ""),
                    card.get("winners_json", "[]"),
                    card.get("losers_json", "[]"),
                    card.get("india_angle", ""),
                    card.get("usa_angle", ""),
                    card.get("china_angle", ""),
                    card.get("personal_impact", ""),
                    card.get("domain_tags", "[]"),
                    card.get("geo_tags", "[]"),
                    card.get("confidence_badge", "medium"),
                    card.get("source_name", ""),
                    card.get("source_url", ""),
                    created_at,
                ),
            )
    logger.info(f"Seeded {len(DEMO_CARDS)} demo cards (is_seed = TRUE)")
    return len(DEMO_CARDS)


def seed_if_empty():
    """
    Deprecated — retained so any old caller fails loudly rather than silently
    injecting fabricated news.

    This used to run automatically on API startup whenever zero live cards existed,
    which meant an LLM outage or an empty pipeline run would quietly repopulate the
    feed with invented stories that were indistinguishable from real output. Seeding
    is now an explicit, deliberate act: `python db/seed.py --demo`.
    """
    logger.warning(
        "seed_if_empty() is deprecated and does nothing. "
        "Run `python db/seed.py --demo` to insert demo cards explicitly."
    )


def clear_seed_cards() -> int:
    """Remove every demo card. Real pipeline output is untouched."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM cards WHERE is_seed = TRUE")
        removed = cur.rowcount
    logger.info(f"Removed {removed} seed cards")
    return removed


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Manage NewsLens demo cards.")
    parser.add_argument("--demo", action="store_true",
                        help="insert the fabricated demo cards (flagged is_seed)")
    parser.add_argument("--clear", action="store_true",
                        help="delete all seed cards, leaving real ones")
    args = parser.parse_args()

    from db.database import init_db
    init_db()

    if args.clear:
        print(f"Removed {clear_seed_cards()} seed cards")
    elif args.demo:
        print(f"Seeded {seed_demo_cards()} demo cards")
    else:
        parser.print_help()
        print("\nNothing done. Seeding is opt-in: these cards are invented news.")
