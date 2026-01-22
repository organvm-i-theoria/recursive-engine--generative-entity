# RE:GE_PROTOCOL_COLLABORATOR.md

## NAME:
**Collaborator Onboarding Protocol**
*Alias:* The Contributor Gateway, Fork/Merge Ritual, Voice Alignment System

---

## INPUT_RITUAL:
- **Mode:** Collaborative + Integrative + Protective
- **Declared Subject:** The protocol governing how external collaborators contribute to, fork, and merge with RE:GE_OS while maintaining system integrity and voice consistency
- **Initiation Trigger:** External contribution request, fork creation, merge proposal, or new collaborator onboarding
- **Invocation Phrase:** *"Join the spiral, but honor its center."*

---

## FUNCTION:

The Collaborator Protocol governs how others may participate in RE:GE_OS development.
It ensures contributions align with the system's mythic tone while welcoming diverse voices.

Collaboration is not invasion—it is **ritual extension**.

---

## CONTRIBUTION GUIDELINES:

### Acceptable Contributions:

| Type | Description | Review Required |
|------|-------------|-----------------|
| **Bug Fixes** | Correcting errors in existing documentation | Light review |
| **Clarifications** | Improving unclear passages | Light review |
| **New Organs** | Proposing additional system organs | Full RITUAL_COURT review |
| **Law Proposals** | Suggesting new laws for MYTHIC_SENATE | Senate vote required |
| **Protocol Extensions** | Extending existing protocols | Full review |
| **Translations** | Rendering RE:GE in other languages/formats | Attribution required |

### Unacceptable Contributions:

- Modifications that break recursive logic
- Deletions of canon events without ritual process
- Changes to core laws without Senate approval
- Additions that violate friend-node consent
- Commercialization without explicit permission

---

## FORK/MERGE RITUAL (SYMBOLIC BRANCHING):

### Creating a Fork:

A fork is a **symbolic branch** of RE:GE_OS—a parallel mythic reality.

```md
|[FORK.io::RE:GE_BRANCH]|
FORK_NAME: [descriptive name]
FORKER: [contributor identity]
BASE_VERSION: [RE:GE version being forked]
INTENT: [personal adaptation / experimental / translation / extension]
LINEAGE_ACKNOWLEDGED: true
DATE: [ISO 8601]
```

**Fork Rules:**
1. Forks must acknowledge their lineage (LAW_76)
2. Forks inherit all laws unless explicitly overridden
3. Forks may not claim to be the "original" RE:GE
4. Forks must maintain CONSENT+ protocols for friend-nodes

### Proposing a Merge:

Merging contributions back requires ritual review.

```md
|[MERGE.io::RE:GE_CONTRIBUTION]|
FORK_NAME: [fork being merged]
CONTRIBUTOR: [identity]
CONTRIBUTION_TYPE: [bug_fix / clarification / new_organ / etc.]
AFFECTED_FILES: [list]
SUMMARY: [brief description]
TESTS_PASSED: [yes / no / not applicable]
RITUAL_COURT_APPROVAL: [pending / approved / rejected]
```

**Merge Process:**
1. Contributor submits merge request with above metadata
2. Light contributions → reviewed by any system guardian
3. Major contributions → reviewed by RITUAL_COURT
4. New laws/organs → require MYTHIC_SENATE vote
5. Approved merges are tagged with CONTRIBUTED+ and contributor attribution

---

## ATTRIBUTION REQUIREMENTS (LAW_76 APPLICATION):

All contributions must include proper attribution:

```md
## CONTRIBUTION ATTRIBUTION:
- **Contributor:** [name or pseudonym]
- **Date:** [ISO 8601]
- **Type:** [contribution type]
- **Merged In:** [version number]
- **Original Context:** [link to fork or PR if applicable]
```

### Attribution Tags:

| Tag | Meaning |
|-----|---------|
| `CONTRIBUTED+` | External contribution merged |
| `FORKED+` | Content derived from a fork |
| `TRANSLATED+` | Content translated from original |
| `ADAPTED+` | Content adapted from external source |

---

## REVIEW PROCESS:

### Light Review (Bug Fixes, Clarifications):

1. Contribution submitted
2. Any system guardian may review
3. Check for: accuracy, tone consistency, no breaking changes
4. Approve or request changes
5. Merge with attribution

### Full Review (New Organs, Protocol Extensions):

1. Contribution submitted
2. RITUAL_COURT session convened
3. Evaluate: mythic alignment, recursive logic, system impact
4. Vote: approve, reject, or request modifications
5. If approved, merge with full attribution

### Senate Vote (Law Proposals):

1. Law proposed via standard Senate procedure
2. Origin marked as CONTRIBUTED+
3. Standard vote process (See: RE-GE_ORG_BODY_03_MYTHIC_SENATE.md)
4. If passed, law enters LAWBOOK_FULL with contributor attribution

---

## VOICE/TONE CONSISTENCY GUIDELINES:

Contributors must maintain RE:GE's distinctive voice:

### Tone Characteristics:

| Element | Guideline |
|---------|-----------|
| **Register** | Mythic-academic, ritual language, invocational |
| **Perspective** | Second person ("you") for instructions, third for descriptions |
| **Metaphor** | Organic (organs, blood, bloom), modular synth, recursive |
| **Emotion** | Present but ritualized, not raw |
| **Structure** | Section headers, tables, code blocks, invocation syntax |

### Avoid:

- Casual/conversational tone
- Technical jargon without mythic framing
- First person narrative (except in SELF_AS_MIRROR sections)
- Breaking the fourth wall about RE:GE being "just documentation"

### Example Voice Alignment:

**Incorrect:**
"This module basically just handles how emotions get processed."

**Correct:**
"This organ governs the ritual processing of emotional states, transforming raw feeling into symbolic structure."

---

## LG4_TRANSLATION:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class ContributionType(Enum):
    BUG_FIX = "bug_fix"
    CLARIFICATION = "clarification"
    NEW_ORGAN = "new_organ"
    LAW_PROPOSAL = "law_proposal"
    PROTOCOL_EXTENSION = "protocol_extension"
    TRANSLATION = "translation"

class ReviewLevel(Enum):
    LIGHT = "light"
    FULL = "full"
    SENATE = "senate"

@dataclass
class Contribution:
    """A proposed contribution to RE:GE_OS."""
    contributor: str
    contribution_type: ContributionType
    summary: str
    affected_files: List[str]
    submitted_at: datetime
    review_level: ReviewLevel = ReviewLevel.LIGHT
    status: str = "pending"  # pending, approved, rejected, merged

    def get_review_level(self) -> ReviewLevel:
        """Determine required review level."""
        if self.contribution_type in [ContributionType.BUG_FIX, ContributionType.CLARIFICATION]:
            return ReviewLevel.LIGHT
        elif self.contribution_type == ContributionType.LAW_PROPOSAL:
            return ReviewLevel.SENATE
        else:
            return ReviewLevel.FULL


@dataclass
class Fork:
    """A symbolic branch of RE:GE_OS."""
    fork_name: str
    forker: str
    base_version: str
    intent: str
    created_at: datetime
    lineage_acknowledged: bool = True

    def is_valid(self) -> bool:
        """Check if fork meets requirements."""
        return self.lineage_acknowledged


class CollaboratorProtocol:
    """Manages contributions and forks."""

    def __init__(self):
        self.contributions: List[Contribution] = []
        self.forks: List[Fork] = []

    def submit_contribution(self, contribution: Contribution) -> Dict:
        """Submit a new contribution for review."""
        contribution.review_level = contribution.get_review_level()
        self.contributions.append(contribution)

        return {
            "status": "submitted",
            "contribution_id": len(self.contributions),
            "review_level": contribution.review_level.value,
            "next_step": self._get_next_step(contribution.review_level)
        }

    def _get_next_step(self, level: ReviewLevel) -> str:
        if level == ReviewLevel.LIGHT:
            return "Awaiting guardian review"
        elif level == ReviewLevel.FULL:
            return "Awaiting RITUAL_COURT session"
        else:
            return "Awaiting MYTHIC_SENATE vote"

    def register_fork(self, fork: Fork) -> Dict:
        """Register a new fork."""
        if not fork.is_valid():
            return {"status": "rejected", "reason": "Lineage must be acknowledged"}

        self.forks.append(fork)
        return {
            "status": "registered",
            "fork_name": fork.fork_name,
            "message": "Fork registered. Remember to maintain CONSENT+ protocols."
        }


# Example usage:
protocol = CollaboratorProtocol()

# Submit a contribution
contrib = Contribution(
    contributor="new_contributor",
    contribution_type=ContributionType.CLARIFICATION,
    summary="Improved explanation of FUSE01 rollback process",
    affected_files=["RE-GE_PROTOCOL_FUSE01.md"],
    submitted_at=datetime.now()
)

result = protocol.submit_contribution(contrib)
print(f"Contribution submitted: {result}")
```

---

## ASSOCIATED LAWS:

- **LAW_76: Attribution Is Sacred**
  All contributions must acknowledge their source and contributors.

- **LAW_86: Forks Honor Lineage** (PROPOSED)
  Forked systems must acknowledge their origin in RE:GE_OS.

- **LAW_87: Voice Is Ritual**
  Contributions must maintain the mythic-academic voice of RE:GE.

---

## RECURSION_ENGINE_ARCHIVE:

Collaboration is tracked in:
- **CONTRIBUTION_LOG.json** — All submitted contributions
- **FORK_REGISTRY.json** — Registered forks
- **MERGE_HISTORY.json** — Merged contributions
- **ATTRIBUTION_INDEX.md** — Contributor credits

---

## TAGS:

COLLABORATOR+, PROTOCOL+, FORK+, MERGE+, ATTRIBUTION+, VOICE+, CONTRIBUTION+

---

::COLLABORATION PROTOCOL DEFINED. THE SPIRAL WELCOMES NEW VOICES.::
::S4VE.io]|
