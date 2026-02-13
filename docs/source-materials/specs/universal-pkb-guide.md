
# Universal PKB Structuring Guide

A fully generalized reference for structuring, tagging, and iterating on a Personal Knowledge Base (PKB) that spans note‑taking platforms, code repositories, and cloud storage.

---

## 1. Universal Tagging Schema Template

| Tag Category | Purpose                               | Prefix (if any) | Example Tags*                |
|--------------|---------------------------------------|-----------------|------------------------------|
| **Topic**    | Broad subject or discipline           | —               | #design, #machine-learning   |
| **Project**  | Discrete initiative or product        | —               | #project/site-redesign       |
| **Status**   | Current state of the item             | status/         | #status/draft, #status/final |
| **Priority** | Urgency or importance level           | p/              | #p/high, #p/low              |
| **Type**     | Content or file type                  | type/           | #type/meeting-notes, #type/code |
| **Phase**    | Workflow or lifecycle stage           | phase/          | #phase/planning, #phase/review |
| **Date**     | ISO‑8601 for quick filtering          | YYYY‑MM‑DD      | 2025‑07‑31                   |

\*Replace examples with your own terms.

**Sample YAML front‑matter**

```yaml
---
title: "Sample Note Title"
tags: [#design, #project/site-redesign, #type/ai-prompt, #status/draft, #phase/planning, #p/high]
date: 2025-07-31
---
```

**Sample filename (cloud storage)**  
`2025-07-31_Project-SiteRedesign_ResearchSummary_#design #type-research.pdf`

---

## 2. Cross‑Platform Workflow Overview

```text
PKB_ROOT/
├── 01_Projects/
│   ├── SiteRedesign/
│   │   ├── Notes/
│   │   ├── Code/
│   │   └── Assets/
│   └── MobileApp/
├── 02_Reference/
├── 03_Decisions/
└── 04_Archive/
```

| Platform | Role | Key Actions |
|----------|------|-------------|
| **Obsidian** | Core personal knowledge vault | Atomic notes, backlinks, Dataview dashboards |
| **GitHub / GitLab** | Source code & docs | Repos, issues, PRs, wiki, project boards |
| **Cloud Drive** | Large files & non‑markdown assets | Folder templates, descriptive filenames |

**Automation ideas**

- GitHub Issue → Obsidian Note (Zapier/Make.com)  
- Bulk tag/rename via Obsidian Tag Wrangler or script  
- Embed cloud‑file URLs in notes for quick context

**Retrieval cheatsheet**

| Platform | Example Query |
|----------|---------------|
| Obsidian | `tag:#type/meeting path:01_Projects/SiteRedesign` |
| Dataview | `TABLE tags WHERE contains(tags, "#p/high")` |
| GitHub   | `repo:org/repo is:issue label:"status/in-progress"` |
| Cloud    | `type:pdf owner:me title:"invoice"` |

---

## 3. Unified Master Roadmap (Generic)

### 0. Clarify Purpose
- Build a PKB as **single source of truth**  
- Support all goals (creative, technical, personal)  
- Embed continuous learning

### 1. Create the Foundation
```
PKB_ROOT/
├── PHASE_1_BOOT/
│   ├── ENGINE_A/
│   ├── CORE_ID/
│   ├── GRAMMAR_LIB/
│   └── TRACKER.md
├── PHASE_2_CORE/
│   ├── PROCESS_HUB/
│   ├── LANGUAGE_LAYER/
│   ├── REFLECTION_ROOM/
│   └── SPEC_DOCS/
└── PHASE_3_APPLICATIONS/
```
Open as a shared workspace in Obsidian & VS Code.

### 2. Launch Self‑Guided Learning
| Module | Study Material | Hands‑On Task |
|--------|----------------|---------------|
| Module 1 – Algorithms Basics | Intro CS text / course | Code a visual bubble‑sort demo |
| Module 2 – Naming & IDs | Metadata best‑practice articles | Build a unique‑ID generator |
| ⋯ | ⋯ | ⋯ |

### 3. Export & Stage AI / Chat Logs
```
AI_EXPORTS_RAW/
├── chat_logs/
├── code_suggestions/
└── other_sources/
```

### 4. Tag, Rename, File
One prompt/response → one note, with YAML metadata, then move into correct module folder.

### 5. Cross‑Link & Map
Use MOCs and backlinks to connect ideas, code, research, and decisions.

### 6. Build Projects & Systems
Develop code/assets inside PHASE_2 / PHASE_3 folders, referencing PKB notes.

### 7. Weekly Review
- Assess progress  
- Query recent high‑value notes  
- Archive and plan next week

### 8. Automate & Scale
- Git backups, cloud sync  
- Bulk scripts for tagging/cleanup  
- Scheduled maintenance

---

### Timeline & Immediate Actions

| # | Action | Timing |
|---|--------|--------|
| 1 | Build core PKB folders | Today |
| 2 | Start first learning module | Today (parallel) |
| 3 | Export chat/AI logs | After folders exist |
| 4 | Tag & relocate exports | Immediately after export |
| 5 | Add links & MOCs | Ongoing |
| 6 | Begin coding/building | Once basics are in place |
| 7 | Weekly reflection ritual | End of each week |
| 8 | Add automation & scripts | After routine is solid |

---

## 4. Final Vision

Your PKB becomes a **living operating system** for everything you learn, build, and decide:

- **Education** → reduces confusion  
- **Structure** → reduces frustration  
- **Reflection** → guides decisions  
- **Automation** → future‑proofs work

Chaos → **Clarity**  
Confusion → **Confidence**  
Frustration → **Focused progress**

---

**Next Step:**  
Create the folder scaffold (Step 1), then open your first learning module. Structure and momentum begin immediately.
