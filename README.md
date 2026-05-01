# 🤖 Build Real-World AI Agents — From Personal Productivity to Enterprise Automation

> A comprehensive, hands-on course for building intelligent AI agents that solve real problems across every domain of work and life.

---

## 🧭 Course Overview

This course takes you from zero to building production-ready AI agents step by step. You won't just learn theory — you'll ship agents that **actually work**, starting with tools you'll use yourself and scaling up to the kinds of systems organizations are actively deploying today.

By the end of this course, you'll have a portfolio of agents spanning personal productivity, creative work, research, and business operations — and the skills to build anything beyond it.

---

## 🗺️ Learning Path

### 🧑‍💻 Phase 1 — Personal Productivity Agents

Build agents that make *your* daily life smarter and faster.

| Agent | Description |
|---|---|
| **Task Prioritizer** | Intelligently ranks and organizes your to-do list based on urgency, impact, and deadlines |
| **Email Summarizer** | Condenses long email threads into clear, actionable summaries |
| **Habit Tracker** | Monitors routines, surfaces patterns, and nudges you toward consistency |
| **Time-Blocking Planner** | Generates optimized daily schedules based on your tasks and energy levels |

---

### ✍️ Phase 2 — Writing, Research & Analysis Agents

Build agents that think, write, and reason on your behalf.

| Agent | Description |
|---|---|
| **Content Generator** | Drafts blog posts, social copy, reports, and more from a brief |
| **Research Synthesizer** | Reads and summarizes complex documents, papers, and web content |
| **Insight Extractor** | Analyzes datasets and surfaces key trends, anomalies, and takeaways |
| **Competitive Intelligence Agent** | Monitors and compares competitors across multiple dimensions |

---

### 🏢 Phase 3 — Business & Enterprise Agents

Build the systems organizations are adopting right now.

| Domain | Agents You'll Build |
|---|---|
| **Operations** | Workflow automators, status reporters, meeting summarizers |
| **Marketing** | Campaign generators, audience segmenters, SEO optimizers |
| **HR** | Job description writers, resume screeners, onboarding assistants |
| **Legal** | Contract reviewers, clause extractors, compliance checkers |
| **Finance** | Expense analyzers, budget forecasters, financial report summarizers |
| **Automation** | Multi-step pipelines, tool-calling agents, scheduled task runners |

---

## 🛠️ What You'll Learn

- **Agent Architecture** — Understand how to design agents with memory, tools, and reasoning loops
- **Prompt Engineering** — Write system prompts that reliably produce structured, useful outputs
- **Tool Use & Function Calling** — Connect agents to APIs, databases, and external services
- **Multi-Agent Pipelines** — Orchestrate multiple specialized agents working in concert
- **Evaluation & Iteration** — Test, debug, and improve agent performance systematically
- **Production Patterns** — Deploy agents safely with guardrails, logging, and error handling

---

## 🧰 Tech Stack

```
Language:     Python 3.11+
LLM Provider: Anthropic Claude (claude-sonnet-4-20250514)
Frameworks:   LangChain / LlamaIndex (optional modules)
Tools:        Function calling, RAG pipelines, vector stores
APIs:         Gmail, Notion, Slack, Google Calendar, and more
Deployment:   FastAPI + Modal / Railway / AWS Lambda
```

---

## 📁 Repository Structure

```
├── 01_personal_productivity/
│   ├── task_prioritizer/
│   ├── email_summarizer/
│   ├── habit_tracker/
│   └── time_blocking_planner/
│
├── 02_writing_research_analysis/
│   ├── content_generator/
│   ├── research_synthesizer/
│   ├── insight_extractor/
│   └── competitive_intelligence/
│
├── 03_business_agents/
│   ├── operations/
│   ├── marketing/
│   ├── hr/
│   ├── legal/
│   ├── finance/
│   └── automation/
│
├── shared/
│   ├── base_agent.py
│   ├── tools/
│   └── utils/
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- An [Anthropic API key](https://console.anthropic.com/)
- Basic Python knowledge

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ai-agents-course.git
cd ai-agents-course

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run Your First Agent

```bash
cd 01_personal_productivity/task_prioritizer
python agent.py
```

---

## 📋 Prerequisites & Who This Is For

This course is designed for:

- **Developers** who want to move beyond hello-world LLM demos into production systems
- **Professionals** who want to automate workflows in their domain (marketing, HR, legal, etc.)
- **Founders & builders** who want to ship AI-powered products fast

You'll need basic Python familiarity. No prior AI/ML experience required.

---

## 📈 Course Outcomes

After completing this course, you will be able to:

- ✅ Design and build agents for any real-world use case
- ✅ Integrate LLMs with APIs, tools, and live data sources
- ✅ Build multi-agent systems that collaborate on complex tasks
- ✅ Evaluate and improve agent reliability in production
- ✅ Deploy agents as services that run autonomously

---

## 🤝 Contributing

Contributions, improvements, and new agent ideas are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-agent`)
3. Commit your changes (`git commit -m 'Add: invoice processing agent'`)
4. Push to the branch (`git push origin feature/new-agent`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## ⭐ Star This Repo

If this course helps you build something useful, give it a star — it helps others discover it too.


