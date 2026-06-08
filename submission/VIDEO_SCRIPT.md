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

### 0:00-0:15 — Проблема і hook

Покажи hero/status area.

Текст озвучки англійською:

> Trust checks are still slow. People open many tools, copy data by hand, and still cannot see why a decision is right. Vartovii changes this into one agent workflow with proof that judges can inspect.

### 0:15-0:40 — Що це за agent

Покажи main UI, live status, model/data/MCP indicators.

Текст озвучки англійською:

> This is Vartovii Trust Intelligence Agent. It is not just a chat screen. It is a Google ADK multi-agent system powered by Gemini. MongoDB Atlas is the memory and evidence layer. MongoDB MCP gives the agent a flexible way to inspect data.

### 0:40-1:15 — Запуск judge path

Натисни або введи:

```text
Run a judge-ready Wirecard investigation. Show route, score, evidence, and decision.
```

Покажи response і проскроль до judge trace section.

Текст озвучки англійською:

> The main agent sends the request to specialist agents. They check company evidence, risk signals, and memory. Then the system saves the result. The UI shows the route, the score, the evidence, and the final decision. A judge can see why the answer was made.

### 1:15-1:50 — Цінність MongoDB Atlas і MCP

Натисни або введи:

```text
Explain how MongoDB Atlas and MCP improve this workflow.
```

Покажи MCP proof section.

Текст озвучки англійською:

> MongoDB Atlas stores companies, crypto projects, wallets, investigations, and audit events. This makes the product more than a one-time answer. MongoDB MCP adds a flexible database specialist. So the agent can answer new questions without us hard-coding every path.

### 1:50-2:25 — Live source proof

Проскроль до Live Proof section, потім перемкнись на `/api/live-proof?slug=ethereum` і `/api/wallet-live-proof`.

Текст озвучки англійською:

> This is the live proof. Vartovii is not only seed data. CoinGecko gives current market data. Etherscan gives a real wallet balance. Both proofs are saved in MongoDB Atlas. The UI shows freshness, score, wallet balance, and storage status.

### 2:25-2:42 — Judge trace і readiness

Перемкнись на `/api/judge-trace`, потім на `/api/readiness`.

Текст озвучки англійською:

> The project also has proof endpoints for judges. Judge trace shows the route, decision, evidence, audit events, and MCP proof. Readiness shows the active model, MongoDB status, test count, Agent Engine path, and MCP setup. This makes the demo easy to verify.

### 2:42-2:55 — Repository і production quality

Перемкнись на GitHub README. Коротко покажи README, architecture, license і tests.

Текст озвучки англійською:

> The repository is public and has an open source license. It includes architecture notes, model policy, source freshness policy, agent roles, deploy scripts, and tests. The goal was to build a real trust system, not a throwaway demo.

### 2:55-3:00 — Закриття

Повернись до UI standalone context section або footer.

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
