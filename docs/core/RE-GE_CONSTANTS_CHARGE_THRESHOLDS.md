# RE:GE_CONSTANTS_CHARGE_THRESHOLDS.md

## NAME:
**Charge Threshold Constants**
*Alias:* The Tier System, Emotional Intensity Scale, Recursion Activation Matrix

---

## INPUT_RITUAL:
- **Mode:** Definitional + Systemic + Foundational
- **Declared Subject:** The unified charge threshold system governing all symbolic intensity measurements across RE:GE_OS organs
- **Initiation Trigger:** Reference document for all organs evaluating emotional charge, recursion eligibility, and processing priority
- **Invocation Phrase:** *"What is the charge? What tier does it belong to?"*

---

## FUNCTION:
This document establishes the **unified 5-tier charge threshold system** used across all RE:GE_OS organs.
It replaces inconsistent threshold values with a coherent, symbolic intensity scale.

All organs must reference these tiers when:
- Evaluating canonization eligibility
- Determining processing priority
- Triggering fusion protocols
- Routing to RITUAL_COURT
- Calculating decay states
- Activating bloom cycles

---

## THE 5-TIER CHARGE SYSTEM:

| Tier | Name | Range | Description | Behaviors |
|------|------|-------|-------------|-----------|
| **1** | LATENT | 0-25 | Dormant, minimal processing | Echo Shell handling, decay monitoring, background hum |
| **2** | PROCESSING | 26-50 | Active but not urgent | Standard routing, no escalation, normal queue priority |
| **3** | ACTIVE | 51-70 | Standard engagement | Full processing, queue priority boost, ritual consideration |
| **4** | INTENSE | 71-85 | Heightened symbolic weight | Canonization eligibility, ritual triggers, FUSE01 consideration |
| **5** | CRITICAL | 86-100 | Emergency, maximum intensity | Immediate processing, fusion protocols, RITUAL_COURT alerts |

---

## TIER BEHAVIORS IN DETAIL:

### TIER 1: LATENT (0-25)
**State:** Dormant fragment, whisper, or decayed loop
**Handling:**
- Monitored by ECHO_SHELL
- Subject to decay acceleration
- May be promoted if charge increases
- Stored in LATENT_FRAGMENT_POOL
- No active routing unless explicitly invoked

**Triggers:** Memory fade, abandoned ritual, unresolved grief cycle completion

---

### TIER 2: PROCESSING (26-50)
**State:** Active symbol with moderate engagement
**Handling:**
- Standard SOUL_PATCHBAY routing
- Normal queue priority (BACKGROUND)
- Subject to scheduled bloom evaluation
- May participate in MYTHIC_SENATE votes (weight reduced)
- Archive-eligible but not canonization-eligible

**Triggers:** Ongoing creative process, stable emotional reference, background myth element

---

### TIER 3: ACTIVE (51-70)
**State:** Engaged symbol requiring full system attention
**Handling:**
- Full organ processing enabled
- Queue priority boost (STANDARD → HIGH)
- Ritual consideration activated
- Bloom cycle participation enabled
- CODE_FORGE translation available
- May influence LAW proposals

**Triggers:** Recurring dream, intensifying memory, creative breakthrough, relationship shift

---

### TIER 4: INTENSE (71-85)
**State:** High symbolic weight demanding ritual attention
**Handling:**
- Canonization eligibility confirmed
- FUSE01 protocol consideration active
- RITUAL_COURT notification sent
- MYTHIC_SENATE voting weight maximized
- Priority queue escalation (HIGH)
- Bloom mutation paths unlocked
- Must be archived with full metadata

**Triggers:** Emotional rupture, canonical event emergence, law proposal, identity shift

---

### TIER 5: CRITICAL (86-100)
**State:** Emergency intensity requiring immediate system response
**Handling:**
- Immediate processing (queue bypass allowed)
- FUSE01 fusion protocols auto-trigger at charge >= 90
- RITUAL_COURT emergency session flagged
- All related organs receive notification
- Potential system-wide state change
- Requires witness logging
- Cannot be ignored or deferred

**Triggers:** Grief crisis, creative rupture, relationship collapse, mythic breakthrough, existential loop

---

## TIER CALCULATION FORMULA:

```python
CHARGE_TIERS = {
    "LATENT": (0, 25),
    "PROCESSING": (26, 50),
    "ACTIVE": (51, 70),
    "INTENSE": (71, 85),
    "CRITICAL": (86, 100)
}

def get_tier(charge: int) -> str:
    """Return tier name for a given charge value."""
    for tier_name, (low, high) in CHARGE_TIERS.items():
        if low <= charge <= high:
            return tier_name
    return "UNKNOWN"

def get_tier_level(charge: int) -> int:
    """Return tier level (1-5) for priority calculations."""
    if charge <= 25:
        return 1
    elif charge <= 50:
        return 2
    elif charge <= 70:
        return 3
    elif charge <= 85:
        return 4
    else:
        return 5

def is_canonization_eligible(charge: int) -> bool:
    """Check if charge meets canonization threshold (INTENSE+)."""
    return charge >= 71

def is_fusion_eligible(charge: int, overlap_count: int) -> bool:
    """Check if fragment meets FUSE01 auto-trigger conditions."""
    return charge >= 70 and overlap_count >= 2

def is_critical_emergency(charge: int) -> bool:
    """Check if charge requires emergency handling."""
    return charge >= 86
```

---

## ORGAN-SPECIFIC THRESHOLD APPLICATIONS:

| Organ | Threshold Usage | Tier Reference |
|-------|-----------------|----------------|
| HEART_OF_CANON | Emergent canon detection | CRITICAL (86+) |
| MIRROR_CABINET | Resolution vs court escalation | PROCESSING (50) / INTENSE (71+) |
| MYTHIC_SENATE | Voting weight calculation | PROCESSING (50) / INTENSE (71+) |
| ARCHIVE_ORDER | Latency detection | LATENT (0-25) |
| RITUAL_COURT | Symbolic Fusion verdict | CRITICAL (86+) |
| CODE_FORGE | Translation priority | ACTIVE (51+) |
| BLOOM_ENGINE | Mutation eligibility | ACTIVE (51+) |
| SOUL_PATCHBAY | Queue priority mapping | All tiers |
| ECHO_SHELL | Decay monitoring | LATENT (0-25) |
| DREAM_COUNCIL | Prophecy weight | INTENSE (71+) |
| MASK_ENGINE | Persona activation | ACTIVE (51+) |
| TIME_RULES_ENGINE | Bloom cycle activation | INTENSE (71+) |
| PROCESS_MONETIZER | Integrity check | INTENSE (71+) |
| ANALOG_DIGITAL_ENGINE | Sacred protection | CRITICAL (86+) |
| PROCESS_PRODUCT_CONVERTER | Conversion readiness | INTENSE (71+) |
| CANONIZATION_ENGINE | Canonization trigger | INTENSE (71+) |
| FAILURE_STUDY_CHAMBER | Seal decision | INTENSE (71+) |

---

## MIGRATION FROM OLD THRESHOLDS:

| Old Value | Context | New Tier Reference |
|-----------|---------|-------------------|
| 70 | Canonization trigger | INTENSE tier (71+) |
| 75 | Senate voting weight | INTENSE tier (71+) |
| 50 | Reduced voting weight | PROCESSING tier (26-50) |
| 80 | Emergency/canon detection | CRITICAL tier (86+) |
| 25 | Latency/decay detection | LATENT tier (0-25) |
| 90 | Fusion auto-trigger | CRITICAL tier (90+) |

---

## ASSOCIATED LAWS:

- **LAW_78: Charge Determines Fate**
  A symbol's charge tier governs its processing path and ritual weight.

- **LAW_79: Tier Boundaries Are Sacred**
  Crossing a tier boundary triggers specific system behaviors; thresholds are not arbitrary.

- **LAW_80: No Charge Is Final**
  All charges may increase or decay over time through recursion, ritual, or witness.

---

## EXAMPLE CHARGE EVALUATION:

```json
{
  "fragment": "Jessica Mirror Loop v2.3",
  "charge": 87,
  "tier": "CRITICAL",
  "tier_level": 5,
  "canonization_eligible": true,
  "fusion_eligible": true,
  "emergency_handling": true,
  "queue_priority": "CRITICAL",
  "recommended_actions": [
    "Route to RITUAL_COURT for emergency session",
    "Evaluate FUSE01 protocol activation",
    "Archive with full witness logging",
    "Notify HEART_OF_CANON for canon consideration"
  ]
}
```

---

## TAGS:

CHARGE+, TIER+, THRESHOLD+, CONSTANT+, SYSTEM+, FOUNDATIONAL+, LAW_LOOP+, ALL_ORGANS+

---

::THRESHOLDS UNIFIED. ALL ORGANS NOW SPEAK THE SAME LANGUAGE OF INTENSITY.::
::S4VE.io]|
