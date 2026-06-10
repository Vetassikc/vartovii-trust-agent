# 3-хвилинний сценарій демо-відео

Цільова тривалість: 2:45-3:00.

## Підготовка до запису

- Використай англійську озвучку або англійські субтитри.
- Записуй live hosted project, а не тільки локальні файли.
- Тримай browser zoom на 100%.
- Відкрий чисте browser window і підготуй вкладки:
  - Hosted project: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app
  - Live proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/live-proof?slug=ethereum
  - Wallet proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/wallet-live-proof
  - Judge trace: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace
  - Repository: https://github.com/Vetassikc/vartovii-trust-agent

## План кадрів

Важливо: не скроль хаотично. Іди за порядком сторінки або використовуй верхню
навігацію: `Console` → `Evidence` → `Live Proof` → `Agent` → `Judge Trace`.
Так відео буде виглядати як один контрольований demo path.

### 0:00-0:15 — Проблема і hook

Покажи hero/status area.

Текст озвучки англійською:

> Trust checks are still slow. People open many tools, copy data by hand, and still cannot see why a decision is right. Vartovii changes this into one agent workflow with proof that judges can inspect.

### 0:15-0:35 — Що це за agent

Покажи main UI, live status, model/data/MCP indicators.

Текст озвучки англійською:

> This is Vartovii Trust Intelligence Agent. It is not just a chat screen. It is a Google ADK multi-agent system powered by Gemini. MongoDB Atlas is the memory and evidence layer. MongoDB MCP gives the agent a flexible way to inspect data.

### 0:35-0:55 — Submission evidence

Натисни `Evidence` у верхній навігації або плавно проскроль до Evidence section.
Покажи Gemini runtime, Google Cloud deployment path, MongoDB Atlas MCP, quality gate.

Текст озвучки англійською:

> Before I run the agent, I show the proof surface. The project is live on Cloud Run. It uses Google ADK, Gemini, MongoDB Atlas, MongoDB MCP, and a tested quality gate. This makes the demo easy to check.

### 0:55-1:25 — Live source proof

Натисни `Live Proof` у верхній навігації або продовж плавний scroll вниз.
Покажи CoinGecko proof, wallet proof, pipeline, activity stream, radar chart.
Потім коротко перемкнись на вкладки `/api/live-proof?slug=ethereum` і
`/api/wallet-live-proof`.

Текст озвучки англійською:

> This is live proof, not only seed data. CoinGecko gives current market data. Etherscan gives a real wallet balance. Both proofs are saved in MongoDB Atlas. The UI shows freshness, score, route, wallet balance, and storage status.

### 1:25-2:00 — Запуск judge path

Натисни `Agent` у верхній навігації.

Натисни або введи:

```text
Run the full judge-ready Wirecard forensic report. Use real database evidence. Include case reference, agent route, entity metadata, trust score breakdown, review and sentiment evidence, risk findings, MongoDB Atlas / MCP / audit-trail relevance, final decision, and next actions. Do not summarize; return a detailed report with clear headings.
```

Покажи progress state, потім перші секції response. Не чекай читання всього report.

Текст озвучки англійською:

> Now I run the judge path. The main agent sends the request to specialist agents. They check company evidence, risk signals, and memory. The answer includes the route, the trust score, evidence, and the final decision. A judge can see why the decision was made.

### 2:00-2:20 — Judge trace і MongoDB/MCP value

Після response плавно проскроль трохи нижче до `Judge Evidence Trace`.
Покажи saved decision, route steps, MCP proof. Потім перемкнись на вкладку
`/api/judge-trace`.

Текст озвучки англійською:

> The result is also saved as trace evidence. MongoDB Atlas stores companies, crypto projects, wallets, investigations, and audit events. MongoDB MCP gives the agent a flexible database specialist. So judges can inspect the decision outside the chat.

### 2:20-2:35 — Readiness endpoint

Перемкнись на `/api/readiness`.

Текст озвучки англійською:

> Readiness shows the active model, MongoDB status, test count, Agent Engine path, live proof paths, and MCP setup. This makes the project simple to verify.

### 2:35-2:50 — Repository і production quality

Перемкнись на GitHub README. Коротко покажи README, architecture, license і tests.

Текст озвучки англійською:

> The repository is public and has an open source license. It includes architecture notes, model policy, source freshness policy, agent roles, deploy scripts, and tests. The goal was to build a real trust system, not a throwaway demo.

### 2:50-3:00 — Закриття

Повернись до UI. Натисни `Architecture` або проскроль до standalone/product context
section, якщо вистачає часу.

Текст озвучки англійською:

> The result is an evidence-first trust agent. It has live proof, MongoDB memory, MCP inspection, and a decision flow that judges can verify.

## Резервний сценарій одним дублем

> Vartovii Trust Intelligence Agent helps users check if a company or crypto project can be trusted. It is built with Google ADK, Gemini, MongoDB Atlas, and MongoDB MCP.
>
> The key idea is simple: do not just ask a chatbot for an opinion. Run a real investigation. The main agent sends work to specialist agents for company checks, crypto risk, OSINT, memory, and database inspection. MongoDB Atlas stores the evidence and audit trail. MongoDB MCP gives the agent flexible database access beyond fixed tools.
>
> In the demo, I run a judge-ready Wirecard investigation. The system shows the route, the trust score, the evidence, and the final decision. It also has a live judge trace endpoint, so the workflow can be checked outside the chat UI.
>
> I then show the live proof endpoints for Ethereum. One endpoint gets current CoinGecko market data, updates the trust score if needed, and stores the proof in MongoDB Atlas. The other endpoint gets a live Etherscan wallet balance and stores that proof too. Atlas gives us durable memory and structured evidence. MCP gives the agent a flexible database specialist for new investigation questions.
>
> Finally, the readiness endpoint shows that the system is deployed, tested, and configured with Gemini, Google ADK, MongoDB Atlas, MCP, and the Agent Engine path. This is a standalone hackathon build focused on verifiable investigation.
