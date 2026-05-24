// Vartovii Trust Intelligence Agent Simulator Script

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const demoSelect = document.getElementById('demo-select');
    const promptInput = document.getElementById('prompt-input');
    const runBtn = document.getElementById('run-simulation-btn');
    const telLatency = document.getElementById('tel-latency');
    const telModel = document.getElementById('tel-model');
    const telStatus = document.getElementById('tel-status');
    const telFallback = document.getElementById('tel-fallback');
    const consoleOutput = document.getElementById('console-output');
    const reportContainer = document.getElementById('report-output-container');
    const copyBtn = document.getElementById('copy-report-btn');

    // Network Node Elements
    const nodeOrchestrator = document.getElementById('node-orchestrator');
    const nodeCorporate = document.getElementById('node-corporate');
    const nodeCrypto = document.getElementById('node-crypto');
    const nodeOSINT = document.getElementById('node-osint');
    const lineCorp = document.getElementById('line-corp');
    const lineCrypto = document.getElementById('line-crypto');
    const lineOSINT = document.getElementById('line-osint');

    // Demo Scenarios Data
    const scenarios = {
        corporate: {
            prompt: "Analyze SAP as an employer and check if their reviews reflect key structural challenges.",
            intent: "CORPORATE_DD",
            agent: "corporate",
            model: "Gemini 2.5 Flash",
            latency: "2.1s",
            fallbacks: 0,
            score: 74,
            risk: "Medium Risk",
            riskClass: "warning",
            pillars: [
                { name: "Leadership", score: 72, color: "var(--green)" },
                { name: "Culture & Values", score: 78, color: "var(--green)" },
                { name: "Compensation", score: 68, color: "var(--accent)" },
                { name: "Work-Life Balance", score: 81, color: "var(--cyan)" },
                { name: "Career Growth", score: 70, color: "var(--green)" },
                { name: "Inclusivity", score: 75, color: "var(--green)" }
            ],
            bullets: [
                "<strong>SAP SE Profile</strong>: Trust score calculated from 234 localized employee reviews.",
                "<strong>Core Strengths</strong>: Highly rated work-life balance (81%) and remote/hybrid framework flexibility.",
                "<strong>Key Painpoints</strong>: Corporate bureaucracy slows down product development cycles (68% alignment score).",
                "<strong>Vacancy Intelligence</strong>: Average retention period of tech positions is 4.2 years, showing solid career stability."
            ],
            logs: [
                { type: "system", text: "Initializing ADK agent runner on session: session_corp_99182" },
                { type: "info", text: "User query ingested: 'Analyze SAP as an employer...'" },
                { type: "info", text: "Intent detected: CORPORATE_DD" },
                { type: "system", text: "Orchestrator routing payload to corporate_agent..." },
                { type: "info", text: "Corporate Agent: Active. Loading registered FunctionTools (6)..." },
                { type: "system", text: "Corporate Agent: Executing search_company(query='SAP')" },
                { type: "success", text: "search_company output: Found SAP SE (ID: sap-se, HQ: Walldorf, Germany)" },
                { type: "system", text: "Corporate Agent: Executing get_company_reviews(company_id='sap-se')" },
                { type: "success", text: "get_company_reviews output: Analyzed 234 glassdoor/kununu posts. Sentiments: Positive: 68%, Neutral: 22%, Negative: 10%" },
                { type: "system", text: "Corporate Agent: Executing get_trust_score(company_id='sap-se')" },
                { type: "success", text: "get_trust_score output: Consolidated Trust Score is 74/100" },
                { type: "system", text: "Corporate Agent: Job finished. Returning results to Orchestrator." },
                { type: "info", text: "Orchestrator: Consolidating sub-agent outputs and format routing..." },
                { type: "success", text: "Pipeline complete. Report compiled successfully." }
            ]
        },
        crypto: {
            prompt: "Give me the full trust assessment for Uniswap and check major holders.",
            intent: "CRYPTO_DD",
            agent: "crypto",
            model: "Gemini 2.5 Flash",
            latency: "1.9s",
            fallbacks: 0,
            score: 82,
            risk: "Low Risk",
            riskClass: "success",
            pillars: [
                { name: "Tokenomics Stability", score: 85, color: "var(--cyan)" },
                { name: "Code Audits", score: 92, color: "var(--cyan)" },
                { name: "Developer Activity", score: 76, color: "var(--green)" },
                { name: "TVL Core Strength", score: 88, color: "var(--cyan)" },
                { name: "Community Sentiment", score: 70, color: "var(--green)" },
                { name: "Governance Safety", score: 65, color: "var(--accent)" }
            ],
            bullets: [
                "<strong>Uniswap Protocol</strong>: High overall Trust Score (82) backed by world-class audits.",
                "<strong>Liquidity Stability</strong>: $5.2B TVL is highly stable with low fluctuation over a 90-day period.",
                "<strong>Token Distribution</strong>: Top 10 address holders own 42.1% of circulating supply, presenting low centralisation risks.",
                "<strong>Development Activity</strong>: Uniswap core Github repo registers 152 commits in the last 30 days."
            ],
            logs: [
                { type: "system", text: "Initializing ADK agent runner on session: session_crypto_44021" },
                { type: "info", text: "User query ingested: 'Give me the full trust assessment for Uniswap...'" },
                { type: "info", text: "Intent detected: CRYPTO_DD" },
                { type: "system", text: "Orchestrator routing payload to crypto_agent..." },
                { type: "info", text: "Crypto Agent: Active. Loading registered FunctionTools (6)..." },
                { type: "system", text: "Crypto Agent: Executing search_crypto_projects(query='Uniswap')" },
                { type: "success", text: "search_crypto_projects output: Found Uniswap Protocol (UNI, Rank #21, TVL: $5.2B)" },
                { type: "system", text: "Crypto Agent: Executing get_crypto_trust_score(project_id='uniswap')" },
                { type: "success", text: "get_crypto_trust_score output: Combined Score is 82/100" },
                { type: "system", text: "Crypto Agent: Executing get_token_holders(project_id='uniswap')" },
                { type: "success", text: "get_token_holders output: Found top 10 addresses holding 42.1% of supply. Low threat profile." },
                { type: "system", text: "Crypto Agent: Job finished. Returning results to Orchestrator." },
                { type: "info", text: "Orchestrator: Consolidating sub-agent outputs and format routing..." },
                { type: "success", text: "Pipeline complete. Report compiled successfully." }
            ]
        },
        forensics: {
            prompt: "Audit wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 and inspect transaction history.",
            intent: "CRYPTO_FORENSICS",
            agent: "crypto",
            model: "Gemini 2.5 Flash",
            latency: "1.4s",
            fallbacks: 0,
            score: 95,
            risk: "Low Risk",
            riskClass: "success",
            pillars: [
                { name: "Balance Security", score: 99, color: "var(--cyan)" },
                { name: "Transaction Pattern", score: 95, color: "var(--cyan)" },
                { name: "Contract Association", score: 92, color: "var(--cyan)" },
                { name: "Age of Wallet", score: 100, color: "var(--cyan)" },
                { name: "Known Owner", score: 99, color: "var(--cyan)" },
                { name: "Gas Efficiency", score: 85, color: "var(--cyan)" }
            ],
            bullets: [
                "<strong>Wallet Tagged</strong>: Associated with Vitalik Buterin (vitalik.eth).",
                "<strong>Account History</strong>: Active since Ethereum genesis. Zero malicious transaction signatures detected.",
                "<strong>Balance</strong>: 1,247 ETH (~$4.2M) liquid treasury.",
                "<strong>Interaction Risk</strong>: Zero interactions with Tornado Cash or flagged sanction addresses."
            ],
            logs: [
                { type: "system", text: "Initializing ADK agent runner on session: session_foren_00281" },
                { type: "info", text: "User query ingested: 'Audit wallet 0xd8dA...'" },
                { type: "info", text: "Intent detected: CRYPTO_FORENSICS" },
                { type: "system", text: "Orchestrator routing payload to crypto_agent..." },
                { type: "info", text: "Crypto Agent: Active. Loading registered FunctionTools (6)..." },
                { type: "system", text: "Crypto Agent: Executing check_wallet(address='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')" },
                { type: "success", text: "check_wallet output: Matches tag: Vitalik Buterin. Balance: 1,247 ETH. Risk: None." },
                { type: "system", text: "Crypto Agent: Executing get_transaction_history(address='0xd8dA...')" },
                { type: "success", text: "get_transaction_history output: Analyzed last 10 transactions. Normal behavior." },
                { type: "system", text: "Crypto Agent: Job finished. Returning results to Orchestrator." },
                { type: "info", text: "Orchestrator: Consolidating sub-agent outputs..." },
                { type: "success", text: "Pipeline complete. Report compiled successfully." }
            ]
        },
        osint: {
            prompt: "Investigate the newly launched AI startup 'PromptForge' founded last week.",
            intent: "UNKNOWN_ENTITY_OSINT",
            agent: "osint",
            model: "Gemini 2.5 Flash",
            latency: "2.8s",
            fallbacks: 0,
            score: 52,
            risk: "High Risk",
            riskClass: "danger",
            pillars: [
                { name: "Web Presence", score: 60, color: "var(--green)" },
                { name: "Press Verifiability", score: 55, color: "var(--green)" },
                { name: "Founder Track Record", score: 65, color: "var(--green)" },
                { name: "Capital Backing", score: 70, color: "var(--green)" },
                { name: "Social Proof", score: 30, color: "var(--accent)" },
                { name: "Product Availability", score: 20, color: "var(--red)" }
            ],
            bullets: [
                "<strong>Entity Status</strong>: Unregistered in core corporate databases. Classified as unknown. OSINT triggered.",
                "<strong>Founding Team</strong>: Alex Chen (ex-Google) and Elena Rostova (ex-Stripe). Decent background score.",
                "<strong>Capital Raised</strong>: $1.2M Pre-seed led by AI Capital. Confirmed through press announcements.",
                "<strong>Recommendation</strong>: High Risk (52/100) due to extremely low maturity, no product available, and minimal digital footprints."
            ],
            logs: [
                { type: "system", text: "Initializing ADK agent runner on session: session_osint_7716" },
                { type: "info", text: "User query ingested: 'Investigate PromptForge...'" },
                { type: "warning", text: "Database lookup: 'PromptForge' - No corporate records found. Downshifting to OSINT fallback..." },
                { type: "info", text: "Intent detected: UNKNOWN_ENTITY_OSINT" },
                { type: "system", text: "Orchestrator routing payload to osint_agent..." },
                { type: "info", text: "OSINT Agent: Active. Triggering Google Search Grounding..." },
                { type: "system", text: "OSINT Agent: Executing GoogleSearchTool(query='PromptForge AI startup founders launch 2026')" },
                { type: "success", text: "GoogleSearchTool output: 3 matches found. Founded May 18, 2026. Raised $1.2M led by AI Capital." },
                { type: "system", text: "OSINT Agent: Computing signals..." },
                { type: "success", text: "Formulated entity score 52/100." },
                { type: "system", text: "OSINT Agent: Job finished. Returning results to Orchestrator." },
                { type: "info", text: "Orchestrator: Consolidating OSINT data..." },
                { type: "success", text: "Pipeline complete. Report compiled successfully." }
            ]
        },
        fallback: {
            prompt: "Analyze SAP as an employer and check if their reviews reflect key structural challenges.",
            intent: "CORPORATE_DD (OUTAGE SIMULATION)",
            agent: "corporate",
            model: "Gemini 2.0 Flash",
            latency: "3.9s",
            fallbacks: 2,
            score: 74,
            risk: "Medium Risk",
            riskClass: "warning",
            pillars: [
                { name: "Leadership", score: 72, color: "var(--green)" },
                { name: "Culture & Values", score: 78, color: "var(--green)" },
                { name: "Compensation", score: 68, color: "var(--accent)" },
                { name: "Work-Life Balance", score: 81, color: "var(--cyan)" },
                { name: "Career Growth", score: 70, color: "var(--green)" },
                { name: "Inclusivity", score: 75, color: "var(--green)" }
            ],
            bullets: [
                "<strong>SLA Outage Resiliency</strong>: High latency (3.9s) caused by 2 API failures. Seamlessly downshifted to gemini-2.0-flash.",
                "<strong>Data Core</strong>: Trust score matches the standard SAP profile, executed using cached tool responses.",
                "<strong>Recovery</strong>: Tenacity module completed retry checks without throwing exceptions to the client."
            ],
            logs: [
                { type: "system", text: "Initializing ADK agent runner on session: session_outage_09281" },
                { type: "info", text: "User query ingested: 'Analyze SAP as an employer...'" },
                { type: "info", text: "Requesting from Primary Model: gemini-2.5-pro..." },
                { type: "error", text: "API Error (503 Service Unavailable). Initiating fallback chain..." },
                { type: "warning", text: "Model downshifted. Requesting from Fallback Model: gemini-2.5-flash..." },
                { type: "error", text: "API Error (503 Service Unavailable). Initiating fallback chain..." },
                { type: "warning", text: "Model downshifted. Requesting from Ultimate Backup Model: gemini-2.0-flash..." },
                { type: "success", text: "Connection established with gemini-2.0-flash." },
                { type: "info", text: "Intent detected: CORPORATE_DD" },
                { type: "system", text: "Orchestrator routing payload to corporate_agent..." },
                { type: "system", text: "Corporate Agent: Executing search_company(query='SAP')" },
                { type: "success", text: "search_company output: Found SAP SE (ID: sap-se)" },
                { type: "system", text: "Corporate Agent: Executing get_trust_score(company_id='sap-se')" },
                { type: "success", text: "get_trust_score output: Score is 74/100" },
                { type: "system", text: "Corporate Agent: Job finished. Returning results to Orchestrator." },
                { type: "success", text: "Pipeline complete. Report compiled successfully." }
            ]
        }
    };

    // Change Prompt on scenario select
    demoSelect.addEventListener('change', () => {
        const val = demoSelect.value;
        if (scenarios[val]) {
            promptInput.value = scenarios[val].prompt;
        }
    });

    // Run Simulation Function
    runBtn.addEventListener('click', () => {
        let val = demoSelect.value;
        const customPromptText = promptInput.value.trim().toLowerCase();

        // Simple heuristic router for custom text inputs
        if (customPromptText !== scenarios[val].prompt.trim().toLowerCase()) {
            val = "osint"; // Default custom queries to OSINT search
            if (customPromptText.includes("sap") || customPromptText.includes("company") || customPromptText.includes("employer") || customPromptText.includes("startup")) {
                val = "corporate";
            }
            if (customPromptText.includes("uniswap") || customPromptText.includes("crypto") || customPromptText.includes("wallet") || customPromptText.includes("0x") || customPromptText.includes("token")) {
                if (customPromptText.includes("0x") || customPromptText.includes("wallet")) {
                    val = "forensics";
                } else {
                    val = "crypto";
                }
            }
        }

        const data = scenarios[val];
        executeSimulation(data);
    });

    function executeSimulation(data) {
        // Reset visual state
        document.body.classList.add('loading');
        runBtn.disabled = true;
        
        telLatency.innerText = "--";
        telModel.innerText = "--";
        telStatus.innerText = "RUNNING";
        telFallback.innerText = "--";

        // Reset Console & Output
        consoleOutput.innerHTML = '<div class="console-line system">[SYSTEM] Pipeline execution started. Routing intent...</div>';
        reportContainer.innerHTML = `
            <div class="output-placeholder">
                <svg class="placeholder-icon spin-icon" style="display: block; width: 2.5rem; height: 2.5rem; animation: rotate 1.5s infinite linear;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                </svg>
                <p>Analyzing signals, resolving API dependencies and generating structured reports...</p>
            </div>
        `;

        // Clear active nodes & lines
        [nodeCorporate, nodeCrypto, nodeOSINT].forEach(n => n.classList.remove('active'));
        [lineCorp, lineCrypto, lineOSINT].forEach(l => l.classList.remove('active'));

        let logIndex = 0;
        const totalLogs = data.logs.length;
        const durationPerLog = 350; // ms per log

        // Pulse Orchestrator initially
        nodeOrchestrator.classList.add('active');

        // Log typing animation loop
        const interval = setInterval(() => {
            if (logIndex < totalLogs) {
                const log = data.logs[logIndex];
                addConsoleLine(log.type, log.text);

                // Activate network visualization parts dynamically based on logs
                if (log.text.includes("routing payload to corporate_agent") || log.text.includes("Corporate Agent: Active")) {
                    nodeCorporate.classList.add('active');
                    lineCorp.classList.add('active');
                }
                if (log.text.includes("routing payload to crypto_agent") || log.text.includes("Crypto Agent: Active")) {
                    nodeCrypto.classList.add('active');
                    lineCrypto.classList.add('active');
                }
                if (log.text.includes("OSINT Agent: Active") || log.text.includes("Google Search")) {
                    nodeOSINT.classList.add('active');
                    lineOSINT.classList.add('active');
                }

                // Simulate downshift failures visually
                if (log.text.includes("API Error")) {
                    nodeOrchestrator.classList.remove('active');
                    setTimeout(() => nodeOrchestrator.classList.add('active'), 200);
                }

                logIndex++;
            } else {
                clearInterval(interval);
                completeSimulation(data);
            }
        }, durationPerLog);
    }

    function addConsoleLine(type, text) {
        const time = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        line.innerText = `[${time}] ${text}`;
        consoleOutput.appendChild(line);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    function completeSimulation(data) {
        document.body.classList.remove('loading');
        runBtn.disabled = false;

        // Set Telemetry
        telLatency.innerText = data.latency;
        telModel.innerText = data.model;
        telStatus.innerText = "COMPLETED";
        telFallback.innerText = data.fallbacks;

        // Render Report
        let pillarsHtml = "";
        data.pillars.forEach(p => {
            pillarsHtml += `
                <div class="pillar-row">
                    <div class="pillar-meta">
                        <span class="pillar-name">${p.name}</span>
                        <span class="pillar-score">${p.score}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: 0%; background: ${p.color};"></div>
                    </div>
                </div>
            `;
        });

        let bulletsHtml = "";
        data.bullets.forEach(b => {
            bulletsHtml += `
                <div class="metric-bullet">
                    <div class="bullet-dot"></div>
                    <div class="bullet-text">${b}</div>
                </div>
            `;
        });

        reportContainer.innerHTML = `
            <div class="report-card">
                <div class="report-header">
                    <div class="report-title-block">
                        <h4>Trust Assessment Report</h4>
                        <p>Target entity detected and audited via Vartovii Multi-Agent Engine</p>
                    </div>
                    <div class="report-score-box">
                        <span class="score-lbl">Risk Rating Score</span>
                        <span class="score-num text-${data.riskClass}">${data.score}</span>
                        <span class="badge badge-sm badge-${data.riskClass} report-risk-badge">${data.risk}</span>
                    </div>
                </div>
                <div class="report-grid">
                    <div class="report-section">
                        <h5>
                            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
                            </svg>
                            Pillar Core Scores
                        </h5>
                        <div class="pillar-list">
                            ${pillarsHtml}
                        </div>
                    </div>
                    <div class="report-section">
                        <h5>
                            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                            </svg>
                            Key Security Assertions
                        </h5>
                        <div class="metric-bullet-list">
                            ${bulletsHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Animate progress bars in report card after load
        setTimeout(() => {
            const fills = reportContainer.querySelectorAll('.progress-fill');
            fills.forEach((fill, idx) => {
                fill.style.width = `${data.pillars[idx].score}%`;
            });
        }, 100);
    }

    // Copy Report Event
    copyBtn.addEventListener('click', () => {
        const text = reportContainer.innerText;
        if (text.includes("No report generated")) return;
        
        navigator.clipboard.writeText(text).then(() => {
            const origText = copyBtn.innerHTML;
            copyBtn.innerHTML = "Copied!";
            setTimeout(() => {
                copyBtn.innerHTML = origText;
            }, 1500);
        });
    });
});
