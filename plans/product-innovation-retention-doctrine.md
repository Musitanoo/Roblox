# Product Innovation and Sustainable Retention Doctrine — ExecPlan

## Outcome

Create an authoritative companion to the current GDD that converts two supplied
design analyses into a coherent, testable doctrine for differentiation,
voluntary retention, and 30-day average CCU. The doctrine must preserve the
project's validation-first posture: no design pattern, psychological effect, or
platform recommendation is treated as proof that players will enjoy or return.

This plan authorizes documentation changes only. It does not authorize new
gameplay, analytics collection, persistence, monetization, LiveOps, publication,
or production traffic.

## Inputs

- `Roblox_Top_1_Game_Design_Document_v1.0.md`.
- Founder-provided analysis: innovation through the relationship between the
  fortress, the horde, and the player.
- Founder-provided analysis: general retention, motivation, bias, CCU, session,
  trust, and measurement factors.
- Current product constitution, stage gates, risk register, documentation
  standard, and official-source register.
- Current Roblox Creator Hub documentation and primary behavioral research.

## Truth and ethics boundary

- No game can please every player or guarantee retention.
- “Perfectly addictive” is translated into high voluntary return, durable
  satisfaction, player trust, and clean stopping points.
- Compulsion, impaired control, punitive absence, deceptive scarcity, paid
  uncertainty, artificial session extension, and exploitative social pressure
  are not product goals.
- Psychological effects are design hypotheses with context-dependent effect
  sizes, not deterministic buttons.

## Acceptance criteria

1. A single companion document defines the innovation thesis, simplicity
   constraint, audience strategy, motivational coverage, replayability model,
   and a prioritized innovation portfolio for Roblox Top 1.
2. The document defines 30-day average CCU mathematically and decomposes it into
   acquisition, activation, return frequency, active duration, intentional
   co-play, reliability, and time-distribution drivers without presenting any
   component as a guaranteed causal lever.
3. A gate-specific KPI framework selects no more than three primary metrics at a
   time, with driver metrics, definitions, decision rules, and harm guardrails.
4. An operational catalog covers the relevant motivation principles and common
   behavioral effects from the supplied texts, distinguishing healthy use,
   misuse, and required evidence.
5. Dangerous levers—variable rewards, FOMO, streaks, loss aversion, sunk cost,
   social proof, paid randomness, and artificial friction—have explicit fail
   conditions.
6. Every major innovation is framed as a falsifiable hypothesis with a smallest
   test and a kill/pivot/continue decision.
7. The GDD links to the companion and contains a concise method-and-hypothesis summary;
   the portal, document register, risk register, glossary, and source register
   remain consistent.
8. Sources are primary or official where available, current as of the review
   date, and cited only for claims they support.
9. All relative Markdown links resolve, Markdown is valid UTF-8, repository
   checks and `git diff --check` pass, and no runtime file is changed by this
   plan.
10. The accepted authority is limited to ethics, measurement discipline,
    sequencing, and experimental rules; product mechanics remain explicitly
    identified hypotheses with stable IDs and `UNTESTED` status.
11. Official Roblox D1, D7, D30, session, co-play, and CCU measures are never
    silently redefined. Internal qualified metrics use different names and sit
    beside, not in place of, platform metrics.
12. The innovation sequence proves the autopsy/rematch loop before introducing
    adaptive-horde behavior. P1/P2 concepts are prohibited from implementation
    until their named entry gates pass.
13. Behavioral effects carry an evidence grade; uncited project heuristics are
    not presented as established or Roblox-specific effects.

## Intended files

- Add `docs/PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md`.
- Update `Roblox_Top_1_Game_Design_Document_v1.0.md`.
- Update `docs/README.md`.
- Update `docs/00-governance/DOCUMENT_REGISTER.md`.
- Update `docs/00-governance/RISK_REGISTER.md` and `GLOSSARY.md` only where the
  new doctrine creates a material governance term or risk.
- Update `docs/references/ROBLOX_OFFICIAL_SOURCES.md` with currently verified
  source scope.
- Update this plan with verification evidence and final status.

## Milestones

1. Audit supplied analyses against existing GDD coverage and current sources.
2. Write the doctrine around decision-ready models, not an idea dump.
3. Integrate it into the documentation authority graph.
4. Validate content, links, encoding, repository checks, and diff scope.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Also run a deterministic relative-link and UTF-8 audit over repository Markdown,
and review the full documentation diff. Studio playtesting is not applicable
because no runtime-facing file is changed by this plan.

## Recovery

All changes are additive or scoped documentation edits. If the doctrine
conflicts with the product constitution or an accepted slice contract, preserve
the narrower existing authority, label the proposal as a hypothesis, and record
the conflict instead of silently expanding scope.

## Progress

- 2026-07-15: supplied texts, GDD, governance corpus, current worktree, Roblox
  Creator Hub sources, and primary research sources audited.
- 2026-07-15: accepted doctrine created with a CCU identity and driver model,
  gate-specific KPI sets, behavioral-effect guardrails, prioritized innovation
  hypotheses, replayability rules, and an experimentation protocol.
- 2026-07-15: GDD, documentation portal, document register, risk register,
  glossary, and official-source register integrated. The durable corpus now
  explicitly excludes disposable `tmp/` prototypes and registers the active 3D
  and retention plans.
- 2026-07-15: `scripts/check.ps1` passed with 0 errors, 0 warnings, and 0 parse
  errors; `git diff --check` passed. A strict audit of 33 durable Markdown files
  found 0 broken relative links, 0 UTF-8 errors, and 0 unregistered documents.
  Studio testing was not applicable because this plan changed documentation
  only. Pre-existing and concurrently changing gameplay/asset work remains
  outside this plan and was not modified or claimed.
- 2026-07-15: critical review reopened the doctrine to separate normative
  method from product hypotheses, protect official metric definitions, replace
  vague composite outcomes, sequence autopsy before adaptive horde, and grade
  the behavioral evidence.
- 2026-07-15: correction complete. Official Roblox metrics retain their names
  and definitions; local diagnostics use `RT1_*`; the opaque “durable
  satisfaction” aggregate was removed; CCU30 uses a time-weighted identity;
  behavioral entries carry `B`/`C` evidence grades; innovation hypotheses have
  stable IDs and gates; only `H-FAILURE-001` is currently prioritized. The GDD
  no longer labels the full future vision canonical or definitive.
- 2026-07-15: post-correction verification passed: repository checks and
  `git diff --check` pass; 33 durable Markdown files have 0 broken relative
  links, 0 UTF-8 errors, and 0 unregistered files.

## Status

Complete. The methodological contract is accepted; all player-response,
behavioral-effect, replayability, pacing, audience, and innovation claims remain
explicit hypotheses. Their product impact remains `UNKNOWN` until the named
tests and gates execute.
