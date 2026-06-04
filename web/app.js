/* ══════════════════════════════════════════════════════════════════
   VARTOVII TRUST INTELLIGENCE DASHBOARD — APPLICATION LOGIC
   Vanilla JS · No frameworks · relative or live API URLs
   ══════════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    // ─── Configuration ───
    const LIVE_API_ORIGIN = 'https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app';
    const API_BASE = window.location.protocol === 'file:' ? LIVE_API_ORIGIN : '';
    const apiUrl = (path) => `${API_BASE}${path}`;

    const API = {
        health:         apiUrl('/api/health'),
        stats:          apiUrl('/api/stats'),
        leaderboard:    apiUrl('/api/leaderboard'),
        investigations: apiUrl('/api/investigations'),
        audit:          apiUrl('/api/audit'),
        readiness:      apiUrl('/api/readiness'),
        judgeTrace:     apiUrl('/api/judge-trace'),
        chat:           apiUrl('/api/chat'),
        entityCompany:  apiUrl('/api/entity/company/'),
        entityCrypto:   apiUrl('/api/entity/crypto/'),
    };

    const REFRESH_INTERVAL = 60_000; // 60 seconds
    const HEALTH_INTERVAL  = 15_000; // 15 seconds

    // ─── Session Management ───
    function getSessionId() {
        let id = localStorage.getItem('vartovii_session_id');
        if (!id) {
            id = crypto.randomUUID
                ? crypto.randomUUID()
                : 'xxxx-xxxx-xxxx-xxxx'.replace(/x/g, () =>
                    ((Math.random() * 16) | 0).toString(16)
                );
            localStorage.setItem('vartovii_session_id', id);
        }
        return id;
    }
    const SESSION_ID = getSessionId();

    // ─── State ───
    let currentLeaderboardType = 'companies';
    let refreshCountdown = 60;
    let isChatBusy = false;

    // ─── DOM References ───
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ─── Utility: Fetch with timeout & error handling ───
    async function apiFetch(url, options = {}) {
        const { timeoutMs = 30_000, ...fetchOptions } = options;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const res = await fetch(url, { ...fetchOptions, signal: controller.signal });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } finally {
            clearTimeout(timeout);
        }
    }

    // ─── Utility: Animate counter ───
    function animateCounter(el, target, duration = 1200) {
        if (el._animFrame) cancelAnimationFrame(el._animFrame);
        const start = performance.now();
        const from = 0;
        const isFloat = !Number.isInteger(target);

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4); // easeOutQuart
            const current = from + (target - from) * eased;
            el.textContent = isFloat
                ? current.toFixed(1)
                : Math.round(current).toLocaleString();
            if (progress < 1) {
                el._animFrame = requestAnimationFrame(tick);
            }
        }
        el._animFrame = requestAnimationFrame(tick);
    }

    // ─── Utility: Simple markdown → HTML ───
    function renderMarkdown(text) {
        if (!text) return '';
        let html = text
            // Escape HTML
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')

            // Code blocks (```)
            .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')

            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')

            // Bold
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

            // Italic
            .replace(/\*(.+?)\*/g, '<em>$1</em>')

            // Headers (### → h4, ## → h3, # → h2)
            .replace(/^#### (.+)$/gm, '<h5>$1</h5>')
            .replace(/^### (.+)$/gm, '<h4>$1</h4>')
            .replace(/^## (.+)$/gm, '<h3>$1</h3>')
            .replace(/^# (.+)$/gm, '<h2>$1</h2>')

            // Horizontal rule
            .replace(/^---$/gm, '<hr>')

            // Unordered lists
            .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')

            // Ordered lists
            .replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Wrap consecutive <li> in <ul>
        html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');

        // Paragraphs — lines that aren't wrapped in block tags
        html = html
            .split('\n')
            .map(line => {
                const trimmed = line.trim();
                if (!trimmed) return '';
                if (/^<(h[1-6]|ul|ol|li|pre|hr|blockquote)/.test(trimmed)) return trimmed;
                return `<p>${trimmed}</p>`;
            })
            .join('\n');

        return html;
    }

    // ─── Utility: Risk level → CSS class suffix ───
    function riskClass(level) {
        return (level || '').toLowerCase().replace(/[^a-z]/g, '');
    }

    // ─── Utility: Trust score → color ───
    function trustColor(score) {
        if (score >= 70) return '#70b783';
        if (score >= 50) return '#d6b56d';
        if (score >= 30) return '#c7864b';
        return '#d46a59';
    }

    // ─── Utility: Trust score → value class ───
    function trustValueClass(score) {
        if (score >= 70) return 'stat-card__value--green';
        if (score >= 50) return 'stat-card__value--yellow';
        if (score >= 30) return 'stat-card__value--orange';
        return 'stat-card__value--red';
    }

    // ─── Utility: Format timestamp ───
    function formatTime(ts) {
        if (!ts) return '';
        const d = new Date(ts);
        if (isNaN(d)) return ts;
        const now = new Date();
        const diff = (now - d) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    function shortResourceName(resource) {
        if (!resource) return 'resource pending';
        const parts = resource.split('/').filter(Boolean);
        const id = parts[parts.length - 1] || resource;
        return `reasoningEngine ${id}`;
    }

    function humanStatus(status) {
        return String(status || 'ready')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());
    }

    // ════════════════════════════════════════════════════════════
    //  1. HEALTH CHECK
    // ════════════════════════════════════════════════════════════
    async function checkHealth() {
        const statusEl = $('#api-status');
        const dotEl = statusEl.querySelector('.status-dot');
        const labelEl = statusEl.querySelector('.status-label');
        const sourcePill = $('#data-source-pill');
        try {
            const data = await apiFetch(API.health);
            if (data.mongodb) {
                dotEl.className = 'status-dot status-dot--live';
                labelEl.textContent = 'LIVE';
                if (sourcePill) sourcePill.textContent = 'MongoDB live';
            } else {
                dotEl.className = 'status-dot status-dot--warning';
                labelEl.textContent = 'DEMO DATA';
                if (sourcePill) sourcePill.textContent = 'Mock fallback';
            }
        } catch {
            dotEl.className = 'status-dot status-dot--error';
            labelEl.textContent = 'OFFLINE';
            if (sourcePill) sourcePill.textContent = 'Offline';
        }
    }

    async function loadReadiness() {
        try {
            const data = await apiFetch(API.readiness);
            const sourcePill = $('#data-source-pill');
            if (sourcePill && data.quality?.data_source) {
                sourcePill.textContent = data.quality.data_source === 'mongodb'
                    ? 'MongoDB live'
                    : 'Mock fallback';
            }

            const hostedUrl = data.submission?.hosted_url;
            const hostedLink = $('#hosted-url-link');
            if (hostedUrl && hostedLink) {
                hostedLink.href = hostedUrl;
                hostedLink.textContent = 'Cloud Run live';
            }

            const agentEngine = data.agent_engine || {};
            const agentEngineStatus = $('#agent-engine-status');
            const agentEngineResource = $('#agent-engine-resource');
            const agentEngineBadge = $('#agent-engine-header-badge');
            if (agentEngineStatus) {
                agentEngineStatus.textContent = agentEngine.status === 'deployed'
                    ? 'Deployed'
                    : 'Deployable';
            }
            if (agentEngineResource) {
                agentEngineResource.textContent = shortResourceName(agentEngine.resource);
                agentEngineResource.title = agentEngine.resource || '';
            }
            if (agentEngineBadge) {
                agentEngineBadge.textContent = agentEngine.status === 'deployed'
                    ? 'Agent Engine live'
                    : 'Agent Engine ready';
            }

            const submissionMeta = $('#submission-meta');
            if (submissionMeta) {
                const video = data.submission?.demo_video === 'pending'
                    ? 'video pending'
                    : 'video ready';
                submissionMeta.textContent = `${hostedUrl ? 'Hosted live' : 'Hosted pending'} · ${video}`;
            }

            const requirements = new Map((data.requirements || []).map(item => [item.name, item]));
            const cloudReq = requirements.get('Google Cloud Agent Builder path');
            const mcpReq = requirements.get('Partner MCP server');
            const geminiReq = requirements.get('Gemini-powered AI agent');
            const hostedReq = requirements.get('Hosted production service');

            if ($('#proof-cloud-status') && cloudReq) $('#proof-cloud-status').textContent = humanStatus(cloudReq.status);
            if ($('#proof-cloud-evidence') && cloudReq) $('#proof-cloud-evidence').textContent = cloudReq.evidence;
            if ($('#proof-mcp-status') && mcpReq) $('#proof-mcp-status').textContent = humanStatus(mcpReq.status);
            if ($('#proof-gemini-status') && geminiReq) $('#proof-gemini-status').textContent = humanStatus(geminiReq.status);
            if ($('#proof-quality-status') && hostedReq) $('#proof-quality-status').textContent = humanStatus(hostedReq.status);
        } catch (err) {
            console.warn('Readiness load failed:', err);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  2. STATS
    // ════════════════════════════════════════════════════════════
    async function loadStats() {
        try {
            const data = await apiFetch(API.stats);

            // Animate main counters
            animateCounter($('#stat-companies'), data.total_companies || 0);
            animateCounter($('#stat-crypto'), data.total_crypto_projects || 0);
            animateCounter($('#stat-reviews'), data.total_reviews || 0);
            animateCounter($('#stat-wallets'), data.total_wallets || 0);
            animateCounter($('#stat-investigations'), data.total_investigations || 0);

            // Trust score with color
            const score = data.avg_trust_score || 0;
            const scoreEl = $('#stat-trust-score');
            animateCounter(scoreEl, score);
            scoreEl.className = `stat-card__value ${trustValueClass(score)}`;

            // Risk distribution bar
            const rd = data.risk_distribution || {};
            const total = (rd.CRITICAL || 0) + (rd.HIGH || 0) + (rd.MEDIUM || 0) + (rd.LOW || 0);
            if (total > 0) {
                const pct = (v) => ((v / total) * 100).toFixed(1) + '%';
                $('#risk-critical').style.width = pct(rd.CRITICAL || 0);
                $('#risk-high').style.width = pct(rd.HIGH || 0);
                $('#risk-medium').style.width = pct(rd.MEDIUM || 0);
                $('#risk-low').style.width = pct(rd.LOW || 0);

                $('#risk-critical').querySelector('.riskmeter__tooltip').textContent = `CRITICAL: ${rd.CRITICAL || 0}`;
                $('#risk-high').querySelector('.riskmeter__tooltip').textContent = `HIGH: ${rd.HIGH || 0}`;
                $('#risk-medium').querySelector('.riskmeter__tooltip').textContent = `MEDIUM: ${rd.MEDIUM || 0}`;
                $('#risk-low').querySelector('.riskmeter__tooltip').textContent = `LOW: ${rd.LOW || 0}`;
            }

            // Risk legend
            const legend = $('#risk-legend');
            legend.innerHTML = [
                { label: `Critical (${rd.CRITICAL || 0})`, color: '#d46a59' },
                { label: `High (${rd.HIGH || 0})`, color: '#c7864b' },
                { label: `Medium (${rd.MEDIUM || 0})`, color: '#d6b56d' },
                { label: `Low (${rd.LOW || 0})`, color: '#70b783' },
            ].map(i => `<span class="risk-legend__item"><span class="risk-legend__dot" style="background:${i.color}"></span>${i.label}</span>`).join('');

            // Risk distribution cards
            $('#risk-count-critical').textContent = rd.CRITICAL || 0;
            $('#risk-count-high').textContent = rd.HIGH || 0;
            $('#risk-count-medium').textContent = rd.MEDIUM || 0;
            $('#risk-count-low').textContent = rd.LOW || 0;

            // Fill bars in risk cards
            if (total > 0) {
                $('#risk-fill-critical').style.width = ((rd.CRITICAL || 0) / total * 100) + '%';
                $('#risk-fill-high').style.width = ((rd.HIGH || 0) / total * 100) + '%';
                $('#risk-fill-medium').style.width = ((rd.MEDIUM || 0) / total * 100) + '%';
                $('#risk-fill-low').style.width = ((rd.LOW || 0) / total * 100) + '%';
            }

            const lastSync = $('#last-sync-label');
            if (lastSync) {
                const source = data.source === 'mongodb' ? 'MongoDB' : 'demo data';
                lastSync.textContent = `${source} · synced ${formatTime(new Date().toISOString())}`;
            }

        } catch (err) {
            console.warn('Stats load failed:', err);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  3. CHAT
    // ════════════════════════════════════════════════════════════
    function addChatMessage(role, content, agentName) {
        const messagesEl = $('#chat-messages');
        // Remove welcome card if present
        const welcome = messagesEl.querySelector('.chat-welcome');
        if (welcome) welcome.remove();

        const msg = document.createElement('div');
        msg.className = `chat-msg chat-msg--${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'chat-msg__avatar';
        avatar.textContent = role === 'user' ? 'U' : 'AI';

        const bubble = document.createElement('div');
        bubble.className = 'chat-msg__bubble';

        if (role === 'agent' && agentName) {
            const label = document.createElement('div');
            label.className = 'chat-msg__agent-label';
            label.textContent = agentName;
            bubble.appendChild(label);
        }

        const bodyDiv = document.createElement('div');
        bodyDiv.innerHTML = role === 'agent' ? renderMarkdown(content) : escapeHtml(content);
        bubble.appendChild(bodyDiv);

        msg.appendChild(avatar);
        msg.appendChild(bubble);
        messagesEl.appendChild(msg);

        // Scroll to bottom
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function setTypingIndicator(visible) {
        const el = $('#typing-indicator');
        el.hidden = !visible;
        if (visible) {
            $('#chat-messages').scrollTop = $('#chat-messages').scrollHeight;
        }
    }

    async function sendChatMessage(text) {
        if (!text.trim() || isChatBusy) return;
        isChatBusy = true;
        const sendBtn = $('#chat-send');
        sendBtn.disabled = true;

        addChatMessage('user', text.trim());
        setTypingIndicator(true);

        try {
            const data = await apiFetch(API.chat, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text.trim(),
                    session_id: SESSION_ID,
                }),
                timeoutMs: 90_000,
            });
            setTypingIndicator(false);
            addChatMessage('agent', data.response || 'No response received.', data.agent);
            loadStats();
            loadInvestigations();
            loadAudit();
            loadJudgeTrace();
        } catch (err) {
            setTypingIndicator(false);
            const message = err.name === 'AbortError'
                ? 'The agent request timed out while waiting for the model. Try a narrower prompt or run it again.'
                : `Could not reach the agent. ${err.message}`;
            addChatMessage('agent', `**Error:** ${message}`);
        } finally {
            isChatBusy = false;
            sendBtn.disabled = false;
        }
    }

    function initChat() {
        const input = $('#chat-input');
        const sendBtn = $('#chat-send');

        sendBtn.addEventListener('click', () => {
            sendChatMessage(input.value);
            input.value = '';
            input.style.height = 'auto';
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage(input.value);
                input.value = '';
                input.style.height = 'auto';
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });

        // Quick action buttons
        $$('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.dataset.prompt;
                input.value = prompt;
                sendChatMessage(prompt);
                input.value = '';
            });
        });
    }

    // ════════════════════════════════════════════════════════════
    //  4. JUDGE EXECUTION TRACE
    // ════════════════════════════════════════════════════════════
    async function loadJudgeTrace() {
        const summaryEl = $('#judge-trace-summary');
        const stepsEl = $('#judge-trace-steps');
        const mcpEl = $('#judge-trace-mcp');
        if (!summaryEl || !stepsEl || !mcpEl) return;

        try {
            const data = await apiFetch(API.judgeTrace);
            const decision = data.decision || {};
            const runtime = data.runtime || {};
            const risk = decision.risk_level || 'UNKNOWN';
            const riskCls = riskClass(risk);
            const score = Math.round(decision.trust_score || 0);
            const color = trustColor(score);

            summaryEl.innerHTML = `
                <div class="trace-decision">
                    <div>
                        <span class="trace-label">Saved decision</span>
                        <h3>${escapeHtml(decision.entity_name || 'Judge scenario')}</h3>
                        <p>${escapeHtml(decision.summary || 'Decision summary pending.')}</p>
                    </div>
                    <div class="trace-score" style="color:${color}">${score}</div>
                    <span class="risk-badge risk-badge--${riskCls}">${escapeHtml(risk)}</span>
                </div>
                <div class="trace-runtime">
                    <span>${escapeHtml(runtime.agent_runtime || 'google_adk')}</span>
                    <span>${escapeHtml(runtime.agent_model || 'gemini')}</span>
                    <span>${runtime.mcp_configured ? 'MCP configured' : 'MCP ready'}</span>
                    <span>${escapeHtml(data.source || 'source')}</span>
                </div>
            `;

            stepsEl.innerHTML = (data.trace || []).map(step => `
                <div class="trace-step">
                    <span class="trace-step__num">${String(step.step || '').padStart(2, '0')}</span>
                    <div>
                        <strong>${escapeHtml(step.agent || 'agent')}</strong>
                        <span>${escapeHtml(step.action || '')}</span>
                        <small>${escapeHtml(step.evidence || '')}</small>
                    </div>
                </div>
            `).join('');

            const mcp = data.mcp_proof || {};
            const counts = mcp.collection_counts || {};
            const auditEvents = data.audit_events || [];
            const latestAudit = auditEvents[0] || {};
            mcpEl.innerHTML = `
                <div class="trace-mcp__header">
                    <span class="mcp-proof__tag">MongoDB MCP proof</span>
                    <strong>${escapeHtml(mcp.server || 'mongodb-mcp-server')}</strong>
                </div>
                <p>${escapeHtml(mcp.policy || 'MCP supports ad-hoc Atlas inspection for judge verification.')}</p>
                <div class="trace-counts">
                    <span>${Number(counts.companies || 0)} companies</span>
                    <span>${Number(counts.crypto_projects || 0)} crypto projects</span>
                    <span>${Number(counts.investigations || 0)} investigations</span>
                    <span>${Number(counts.audit_log || 0)} audit events</span>
                </div>
                <div class="trace-audit-sample">
                    <span>Latest audit</span>
                    <strong>${escapeHtml(latestAudit.agent || 'memory_agent')}</strong>
                    <small>${escapeHtml(latestAudit.action || 'audit pending')} · ${escapeHtml(latestAudit.model_used || runtime.agent_model || '')}</small>
                </div>
            `;
        } catch (err) {
            console.warn('Judge trace load failed:', err);
            summaryEl.innerHTML = '<p class="trace-error">Judge trace could not be loaded.</p>';
        }
    }

    // ════════════════════════════════════════════════════════════
    //  5. LEADERBOARD
    // ════════════════════════════════════════════════════════════
    async function loadLeaderboard(type = currentLeaderboardType) {
        currentLeaderboardType = type;
        const tbody = $('#leaderboard-body');
        tbody.innerHTML = `<tr class="leaderboard-loading"><td colspan="5"><div class="loader-dots"><span></span><span></span><span></span></div>Loading…</td></tr>`;

        // Refresh button spin
        const refreshBtn = $('#refresh-btn');
        refreshBtn.classList.add('spinning');
        setTimeout(() => refreshBtn.classList.remove('spinning'), 800);

        try {
            const data = await apiFetch(`${API.leaderboard}?type=${type}&limit=10`);
            const items = data.leaderboard || [];

            if (items.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:2rem">No data available</td></tr>`;
                return;
            }

            tbody.innerHTML = items.map((item, i) => {
                const rank = i + 1;
                const name = type === 'companies'
                    ? (item.company_name || item.name || 'Unknown')
                    : (item.name || item.symbol || 'Unknown');
                const score = Math.round(item.trust_score || 0);
                const risk = item.risk_level || 'UNKNOWN';
                const riskCls = riskClass(risk);
                const color = trustColor(score);

                // Extra info column
                let extra = '';
                if (type === 'companies') {
                    extra = [item.country, item.industry].filter(Boolean).join(' · ');
                } else {
                    const parts = [];
                    if (item.symbol) parts.push(item.symbol);
                    if (item.price_usd != null) parts.push(`$${Number(item.price_usd).toLocaleString(undefined, {maximumFractionDigits: 2})}`);
                    extra = parts.join(' · ');
                }

                // Rank badge class
                let rankCls = 'rank-badge--default';
                if (rank === 1) rankCls = 'rank-badge--1';
                else if (rank === 2) rankCls = 'rank-badge--2';
                else if (rank === 3) rankCls = 'rank-badge--3';

                const slug = type === 'companies'
                    ? (item.profile_slug || item.slug || name.toLowerCase().replace(/\s+/g, '-'))
                    : (item.slug || name.toLowerCase().replace(/\s+/g, '-'));

                return `
                    <tr data-type="${type}" data-slug="${slug}">
                        <td><div class="rank-badge ${rankCls}">${rank}</div></td>
                        <td>
                            <div class="entity-name">${escapeHtml(name)}</div>
                            ${extra ? `<div class="entity-sub">${escapeHtml(extra)}</div>` : ''}
                        </td>
                        <td>
                            <div class="trust-score-cell">
                                <span class="trust-score-num" style="color:${color}">${score}</span>
                                <div class="trust-bar">
                                    <div class="trust-bar__fill" style="width:${score}%;background:${color}"></div>
                                </div>
                            </div>
                        </td>
                        <td><span class="risk-badge risk-badge--${riskCls}">${risk}</span></td>
                        <td class="entity-detail-hint">${extra ? escapeHtml(extra) : '—'}</td>
                    </tr>
                `;
            }).join('');

            // Click handlers for entity detail
            tbody.querySelectorAll('tr[data-slug]').forEach(row => {
                row.addEventListener('click', () => {
                    const slug = row.dataset.slug;
                    const rowType = row.dataset.type;
                    openEntityModal(rowType, slug);
                });
            });

        } catch (err) {
            console.warn('Leaderboard load failed:', err);
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:2rem">Failed to load leaderboard</td></tr>`;
        }
    }

    function initLeaderboardTabs() {
        $$('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('.tab-btn').forEach(b => b.classList.remove('tab-btn--active'));
                btn.classList.add('tab-btn--active');
                loadLeaderboard(btn.dataset.tab);
            });
        });

        $('#refresh-btn').addEventListener('click', () => {
            refreshCountdown = 60;
            loadLeaderboard();
        });
    }

    // Auto-refresh countdown
    function startRefreshTimer() {
        setInterval(() => {
            refreshCountdown--;
            const timerEl = $('#refresh-timer');
            if (refreshCountdown <= 0) {
                refreshCountdown = 60;
                loadLeaderboard();
                loadStats();
                loadInvestigations();
                loadAudit();
            }
            timerEl.textContent = `Auto-refresh in ${refreshCountdown}s`;
        }, 1000);
    }

    // ════════════════════════════════════════════════════════════
    //  6. ENTITY DETAIL MODAL
    // ════════════════════════════════════════════════════════════
    async function openEntityModal(type, slug) {
        const modal = $('#entity-modal');
        const body = $('#modal-body');
        body.innerHTML = '<div class="loader-dots"><span></span><span></span><span></span></div>';
        modal.showModal();

        const url = type === 'companies' || type === 'company'
            ? API.entityCompany + slug
            : API.entityCrypto + slug;

        try {
            const data = await apiFetch(url);
            body.innerHTML = renderEntityDetail(data.entity || data, data.entity_type || type);
        } catch (err) {
            body.innerHTML = `<p style="color:var(--text-muted)">Could not load entity details. ${err.message}</p>`;
        }
    }

    function renderReview(review) {
        if (typeof review === 'string') return escapeHtml(review);

        const title = review.title || review.summary || review.text || 'Review';
        const meta = [
            review.source,
            review.rating != null ? `${review.rating}/5` : null,
            review.sentiment,
            review.date,
        ].filter(Boolean).map(value => escapeHtml(String(value))).join(' · ');

        const body = review.text && review.text !== title
            ? `<div style="margin-top:0.25rem;color:var(--text-secondary)">${escapeHtml(review.text)}</div>`
            : '';

        return `
            <div style="font-weight:600;color:var(--text-primary)">${escapeHtml(title)}</div>
            ${meta ? `<div style="font-size:0.68rem;color:var(--text-muted);margin-top:0.15rem">${meta}</div>` : ''}
            ${body}
        `;
    }

    function renderEntityDetail(data, type) {
        const name = data.company_name || data.name || 'Entity';
        const score = Math.round(data.trust_score || 0);
        const risk = data.risk_level || 'UNKNOWN';
        const color = trustColor(score);
        const riskCls = riskClass(risk);

        let detailItems = '';
        if (type === 'companies' || type === 'company') {
            detailItems = `
                <div class="detail-item"><div class="detail-label">Country</div><div class="detail-value">${data.country || '—'}</div></div>
                <div class="detail-item"><div class="detail-label">Industry</div><div class="detail-value">${data.industry || '—'}</div></div>
                <div class="detail-item"><div class="detail-label">Trust Score</div><div class="detail-value" style="color:${color}">${score}/100</div></div>
                <div class="detail-item"><div class="detail-label">Risk Level</div><div class="detail-value"><span class="risk-badge risk-badge--${riskCls}">${risk}</span></div></div>
            `;
        } else {
            detailItems = `
                <div class="detail-item"><div class="detail-label">Symbol</div><div class="detail-value">${data.symbol || '—'}</div></div>
                <div class="detail-item"><div class="detail-label">Price USD</div><div class="detail-value">$${Number(data.price_usd || 0).toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-label">Trust Score</div><div class="detail-value" style="color:${color}">${score}/100</div></div>
                <div class="detail-item"><div class="detail-label">Risk Level</div><div class="detail-value"><span class="risk-badge risk-badge--${riskCls}">${risk}</span></div></div>
                <div class="detail-item"><div class="detail-label">Market Cap</div><div class="detail-value">$${Number(data.market_cap || 0).toLocaleString()}</div></div>
            `;
        }

        let reviewsHtml = '';
        if (data.reviews && data.reviews.length > 0) {
            reviewsHtml = `
                <h3 style="margin-top:1rem;font-family:var(--font-display)">Reviews (${data.reviews.length})</h3>
                <div style="max-height:200px;overflow-y:auto;margin-top:0.5rem">
                    ${data.reviews.slice(0, 5).map(r => `
                        <div style="padding:0.5rem;background:rgba(255,255,255,0.02);border-radius:8px;margin-bottom:0.4rem;font-size:0.78rem;color:var(--text-secondary)">
                            ${renderReview(r)}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <h2>${escapeHtml(name)}</h2>
            <div class="detail-grid">${detailItems}</div>
            ${reviewsHtml}
        `;
    }

    function initModal() {
        const modal = $('#entity-modal');
        const closeBtn = $('#modal-close');
        closeBtn.addEventListener('click', () => modal.close());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.close();
        });
    }

    // ════════════════════════════════════════════════════════════
    //  7. INVESTIGATIONS
    // ════════════════════════════════════════════════════════════
    async function loadInvestigations() {
        const timeline = $('#investigations-timeline');
        try {
            const data = await apiFetch(`${API.investigations}?limit=10`);
            const items = data.investigations || [];

            if (items.length === 0) {
                timeline.innerHTML = `
                    <div class="timeline-empty" id="timeline-empty">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="timeline-empty__icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        <p>No investigations yet. Use the chat to trigger one!</p>
                    </div>
                `;
                return;
            }

            timeline.innerHTML = items.map(inv => {
                const risk = inv.risk_level || 'UNKNOWN';
                const riskCls = riskClass(risk);
                const typeIcon = (inv.entity_type || '').toLowerCase().includes('crypto') ? 'CR' : 'CO';
                const score = Math.round(inv.trust_score || 0);
                const color = trustColor(score);

                return `
                    <div class="timeline-item timeline-item--${riskCls}">
                        <div class="timeline-item__header">
                            <span class="timeline-item__type">${typeIcon}</span>
                            <span class="timeline-item__name">${escapeHtml(inv.entity_name || 'Unknown')}</span>
                            <span class="trust-score-num" style="color:${color};font-size:0.75rem">${score}/100</span>
                            <span class="risk-badge risk-badge--${riskCls}">${risk}</span>
                        </div>
                        ${inv.summary ? `<div class="timeline-item__summary">${escapeHtml(inv.summary)}</div>` : ''}
                        <div class="timeline-item__time">${formatTime(inv.timestamp)}</div>
                    </div>
                `;
            }).join('');

        } catch (err) {
            console.warn('Investigations load failed:', err);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  8. AUDIT LOG
    // ════════════════════════════════════════════════════════════
    async function loadAudit() {
        const list = $('#audit-list');
        try {
            const data = await apiFetch(`${API.audit}?limit=20`);
            const events = data.events || [];

            if (events.length === 0) {
                list.innerHTML = '<div style="text-align:center;padding:1rem;color:var(--text-muted);font-size:0.8rem">No audit events yet.</div>';
                return;
            }

            list.innerHTML = events.map(ev => {
                const icon = getAgentIcon(ev.agent);
                return `
                    <div class="audit-entry">
                        <span class="audit-entry__icon">${icon}</span>
                        <span class="audit-entry__agent">${escapeHtml(ev.agent || 'system')}</span>
                        <span class="audit-entry__action">${escapeHtml(ev.action || '')}</span>
                        ${ev.model_used ? `<span class="audit-entry__model">${escapeHtml(ev.model_used)}</span>` : ''}
                        <span class="audit-entry__time">${formatTime(ev.timestamp)}</span>
                    </div>
                `;
            }).join('');

        } catch (err) {
            console.warn('Audit load failed:', err);
            list.innerHTML = '<div style="text-align:center;padding:1rem;color:var(--text-muted);font-size:0.8rem">Failed to load audit log.</div>';
        }
    }

function getAgentIcon(agent) {
        if (!agent) return 'SYS';
        const a = agent.toLowerCase();
        if (a.includes('orchestrat')) return 'OR';
        if (a.includes('corporate') || a.includes('corp')) return 'CO';
        if (a.includes('crypto')) return 'CR';
        if (a.includes('osint')) return 'OS';
        if (a.includes('memory')) return 'ME';
        if (a.includes('mcp')) return 'MC';
        return 'SYS';
    }

    // ════════════════════════════════════════════════════════════
    //  NAVIGATION & UI
    // ════════════════════════════════════════════════════════════
    function initNav() {
        // Burger menu
        const burger = $('#burger-btn');
        const nav = $('.header__nav');
        burger.addEventListener('click', () => {
            const isOpen = nav.classList.toggle('open');
            burger.setAttribute('aria-expanded', isOpen);
        });

        // Close mobile menu on link click
        nav.querySelectorAll('.header__link').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('open');
                burger.setAttribute('aria-expanded', 'false');
            });
        });

        // Active nav link on scroll
        const sections = $$('section[id]');
        const navLinks = $$('.header__link');
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        navLinks.forEach(l => l.classList.remove('header__link--active'));
                        const target = entry.target.id;
                        const activeLink = document.querySelector(`.header__link[href="#${target}"]`);
                        if (activeLink) activeLink.classList.add('header__link--active');
                    }
                });
            },
            { rootMargin: '-20% 0px -60% 0px' }
        );
        sections.forEach(s => observer.observe(s));
    }

    // ════════════════════════════════════════════════════════════
    //  INITIALIZATION
    // ════════════════════════════════════════════════════════════
    function init() {
        // Initial data loads
        checkHealth();
        loadReadiness();
        loadStats();
        loadLeaderboard();
        loadInvestigations();
        loadAudit();
        loadJudgeTrace();

        // Init interactive components
        initChat();
        initLeaderboardTabs();
        initModal();
        initNav();

        // Periodic refreshes
        setInterval(checkHealth, HEALTH_INTERVAL);
        startRefreshTimer();
    }

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
