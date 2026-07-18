# Precanonical Web Image Workflow

## Purpose

This layer turns a gameplay brief and the frozen Salvaged Frontier
constitution into a bounded visual proposal before canonicalization and before
production 3D.

Its authority is deliberately narrow:

> Codex specifies and verifies. ChatGPT Web Images visualizes. A human selects.
> The canon rationalizes. Blender constructs. Roblox Studio proves.

ChatGPT Web Images is a replaceable visualization surface. It is not a
geometry generator, a canon authority or a production gate.

## Why this layer exists

Text-only specifications leave visual gaps, while a single attractive image
can conceal contradictory views, impossible mechanics and invented hidden
geometry. The precanonical layer provides fast visual convergence without
allowing probabilistic output to silently define the object.

It specifically protects:

- gameplay function before decoration;
- Salvaged Frontier identity before generic style imitation;
- bounded Web quota before browser activity;
- provenance before subjective review;
- human authorship before canonicalization;
- deterministic reconstruction before production claims.

## Source contracts

```text
art/precanonical/policy.json
art/precanonical/examples/<asset>-brief.json
assets-3d/<asset>/precanonical/requests/<request-id>/
assets-3d/<asset>/precanonical/results/<result-id>/
```

The policy binds the exact selected constitution SHA-256 and states:

- only `chatgpt_web_images` is allowed in this branch;
- Chrome and the Codex in-app Browser are transport only;
- `codex_chrome` is the default and the only adapter allowed to upload files;
- `codex_iab` is an explicit attachment-free fallback;
- browser-adapter switching is never automatic;
- the provider is replaceable;
- automatic Codex imagegen fallback is forbidden;
- automatic API fallback is forbidden;
- silent retry and unlimited regeneration are forbidden;
- images remain non-canonical and non-production.

## Four bounded stages

### Exploration

One 2×2 sheet compares four silhouette territories under the same scale,
camera and simplified materials. It is used to reject weak massing cheaply.

### Consolidation

One chosen construction is shown from front three-quarter, rear three-quarter
and black silhouette. Views must depict the same object.

### Precanonical board

The selected solution receives the views, states, components, functional zones
and mobile framing required to begin rationalization.

### Correction

One prior result is attached and only explicit corrections are authorized.
Every unmentioned characteristic must remain stable.

Each stage receives a new request ID and prompt hash. A previously successful
prompt cannot be silently submitted again.

## Command sequence

Create a request:

```powershell
.\scripts\art-direction.ps1 precanon-init `
  -Brief .\tools\roblox-art-bible-sota-v3\art\precanonical\examples\defense-barricade-small-brief.json `
  -RequestId defense-barricade-web-001 `
  -Output .\assets-3d\defense-barricade-small\precanonical\requests\defense-barricade-web-001 `
  -PrecanonicalStage exploration `
  -BrowserAdapter codex_iab `
  -MaximumWebGenerations 4
```

Run the zero-consumption preflight:

```powershell
.\scripts\art-direction.ps1 precanon-preflight `
  -Request .\assets-3d\defense-barricade-small\precanonical\requests\defense-barricade-web-001\request.json `
  -Output .\tools\roblox-art-bible-sota-v3\build\precanonical\defense-barricade-web-001\preflight.json
```

Verify the exact app-managed Browser runtime:

```powershell
.\scripts\art-direction.ps1 precanon-browser-doctor `
  -BrowserAdapter codex_iab `
  -Output .\tools\roblox-art-bible-sota-v3\build\precanonical\defense-barricade-web-001\browser-doctor.json
```

Prepare the browser handoff:

```powershell
.\scripts\art-direction.ps1 precanon-handoff `
  -Request .\assets-3d\defense-barricade-small\precanonical\requests\defense-barricade-web-001\request.json `
  -Preflight .\tools\roblox-art-bible-sota-v3\build\precanonical\defense-barricade-web-001\preflight.json `
  -BrowserDoctor .\tools\roblox-art-bible-sota-v3\build\precanonical\defense-barricade-web-001\browser-doctor.json `
  -Output .\tools\roblox-art-bible-sota-v3\build\precanonical\defense-barricade-web-001\handoff.json
```

The preflight ends at `WEB_PREFLIGHT_PASS`. The Browser doctor may prove
`localInstallationStatus=PASS`, but repository tooling cannot prove
current-task tool exposure. The handoff therefore remains
`AWAITING_TASK_BROWSER_CAPABILITY` with `submissionAuthorized=false`. It
consumes no quota and performs no browser action.

After a human-authorized Web submission and download, import the local image:

```powershell
.\scripts\art-direction.ps1 precanon-import `
  -Request <request.json> `
  -ResultId defense-barricade-result-001 `
  -Image <downloaded-image.png> `
  -Output .\assets-3d\defense-barricade-small\precanonical\results\defense-barricade-result-001
```

Record a review:

```powershell
.\scripts\art-direction.ps1 precanon-review `
  -Result <result.json> `
  -RequestId defense-barricade-review-001 `
  -ReviewDecision REVISION_REQUIRED `
  -Output <result-folder>\review.json `
  -Correct "Rear construction is unresolved" `
  -ForbidNext "New components"
```

`HUMAN_SELECTED` additionally requires a named reviewer and an assessment JSON
whose five dimensions all pass. Even then:

```text
canonicalizationAuthorized = true
canonical = false
productionApproved = false
```

The next step is rationalization into the complete multimodal visual canon.

## Browser adapter contract

The request selects one adapter explicitly:

| Adapter | Attachment-free request | Request with references |
| --- | --- | --- |
| `codex_iab` | Allowed | Forbidden by preflight |
| `codex_chrome` | Allowed | Allowed |

`codex_chrome` remains the default. `codex_iab` is a controlled fallback for
attachment-free requests and keeps the same ChatGPT Web provider, prompt,
budget and provenance contracts. Selecting it does not authorize automatic
submission or any API fallback.

Both official adapters are task-scoped Codex capabilities. Plugin installation,
an app-managed `mcp_servers.node_repl` entry, a healthy `js` MCP tool, a native
pipe and a valid Chrome host prove only local runtime health. They do not prove
that the current task capability manifest exposes `mcp__node_repl__js`.

Codex may legitimately regenerate `node_repl`, `NODE_REPL_*`,
`BROWSER_USE_*`, trusted hashes and native-pipe values. Never delete or
hand-edit those app-managed entries, and never copy them between app builds,
machines or tasks.

When actual generation is authorized, Codex may use the selected official
browser control surface to:

1. reuse one authenticated ChatGPT Web tab;
2. insert the exact bound prompt;
3. attach only hash-bound references;
4. request one generation;
5. avoid continuous visual polling;
6. download the result once;
7. return to local-file analysis.

It must not:

- inspect cookies, local storage or account secrets;
- reason or rewrite the prompt inside the browser;
- retry after an error without a new decision;
- claim to know an unobservable remaining quota;
- switch to Codex imagegen or an API automatically;
- invent the internal model name;
- promote the result directly into the canon.

The Web UI is intentionally outside deterministic package verification. If it
changes, the truthful status is `WEB_UI_CHANGED`, not a retry loop.

If the app-managed MCP server exposes `js` but the current task omits
`mcp__node_repl__js`, the truthful state is
`WEB_TASK_CAPABILITY_UNAVAILABLE`. Do not invoke `node_repl` directly from
repository scripts as an undeclared proxy, and do not substitute shell,
Playwright, Computer Use or another browser controller.

For `codex_iab`, step 3 is replaced by a strict assertion that the handoff
contains zero attachments. If a reference becomes necessary, create or update
the request with `codex_chrome`, rerun preflight and obtain fresh user
authorization. Never switch adapters silently.

## Preflight gates

The preflight validates:

- closed request schema;
- exact policy, constitution, brief and prompt hashes;
- selected Salvaged Frontier identity;
- allowed generation surface;
- explicitly allowed browser adapter;
- adapter compatibility with the exact attachment count;
- disabled fallbacks and retries;
- stage-specific view scope;
- remaining per-request budget;
- absence of an imported result with the same prompt hash;
- non-canonical and non-production authority.

It reports the remaining bounded generations but always reports the platform
quota as `UNKNOWN` unless the Web interface explicitly exposes it.

The Browser doctor separately validates:

- the selected official plugin is installed and enabled;
- the app-managed `node_repl` executable exists;
- the selected `iab` or `chrome` backend is declared;
- the MCP server itself exposes the `js` tool;
- the Chrome native-host registration is complete when Chrome is selected.

It always reports current-task exposure as `UNKNOWN`, because only the Codex
host can place `mcp__node_repl__js` in a task's callable capability manifest.

## Official object-by-state campaign route

For the selected Salvaged Frontier corpus, do not ask one image to define
several gameplay states. Build the persistent campaign once:

```powershell
.\scripts\art-direction.ps1 precanon-campaign-init `
  -Output .\assets-3d\precanonical\campaigns\salvaged-frontier-states-v15 `
  -CampaignId salvaged-frontier-states-v15
```

Then run the continuous operator:

```powershell
.\scripts\art-direction.ps1 precanon-campaign-operator `
  -Campaign .\assets-3d\precanonical\campaigns\salvaged-frontier-states-v15\campaign.json `
  -Output .\tools\roblox-art-bible-sota-v3\build\precanonical\salvaged-frontier-states-v15\operator
```

The campaign catalog is compiled from the six selected visual canons in this
stable display order:

```text
barricade       intact -> damaged -> critical
damage_effect   damaged -> critical
enemy_standard  intact -> damaged -> critical
floor_module    intact -> damaged
objective_core  intact -> damaged -> critical
turret_fast_v1  intact -> damaged -> critical
```

This produces exactly sixteen primary tasks. Every task:

- requests one image for one object and one state only;
- requires `gpt-image-2` and visible UI confirmation;
- allows one Web generation in its immutable request;
- produces hero front, rear, black silhouette and Roblox gameplay-camera views
  of the same state inside one 2x2 image;
- forbids any state comparison or mixed state board;
- embeds the state's explicit gameplay-truth boundary and excludes unproven
  capability, collision, persistence, repair and adaptation claims;
- lists the object's operational overlays, transients and terminal state but
  forbids composing them into the primary reference;
- uses object-class-specific identity locks, style rules, negative constraints
  and final output self-checks;
- remains non-canonical and non-production.

The display order is not a production gate. The first state of every
unfinished object is immediately generation-eligible, so the operator may
activate enemy, floor, objective or turret in any order in the current
campaign. All sixteen prompts remain readable and copyable at all times.
Dependent states expose a labelled canonical preview until the accepted
previous state of the same object exists; only then is their exact
continuity-bound transport prompt created.

The first state of an object is constructed from its exact canon. Every later
state attaches the accepted previous state and must transform the same
construction rather than redesign it. `REVISION_REQUIRED` attaches the current
attempt for a targeted edit. `REJECTED` creates a fresh bounded attempt without
using the rejected image as visual authority. Neither path retries
automatically.

After an accepted `PRECANONICAL_CANDIDATE` or `HUMAN_SELECTED` review, the
operator immediately prepares and displays the next state or object. The page
shows progress, every object, every state, attempt counts, recorded previews,
the current task and the next task.

The review form pre-fills its preserve rules from the exact state invariants
bound in `source-brief.json`. When the request has a reviewed continuity
result, its explicit preserve rules appear first and the current state canon
completes them. The reviewer may edit or restore these suggestions, but must
still confirm the five perceptual assessment dimensions. Normal navigation
never overwrites an in-progress human edit, and reviewer identity is available
only for `HUMAN_SELECTED`.

The campaign explorer is deliberately separate from the active production
workspace:

- every state is selectable, including states that have not yet been generated;
- filters isolate remaining, non-generated, generated, review-required,
  accepted or blocked states;
- previous/next controls, keyboard arrows and browser history navigate all
  sixteen tasks without changing `currentTaskId`;
- the selected state exposes its status, catalog position, continuity
  predecessor, accepted decision and complete attempt history;
- every imported attempt remains individually viewable, including rejected or
  revision-required attempts;
- a non-generated state shows an explicit reserved placeholder and its unlock
  dependency instead of a disabled or blank control;
- deep links use `?task=<taskId>&attempt=<index>&filter=<filter>` while the
  non-persisted operator token remains in the URL fragment;
- `Revenir à la tâche active` restores the production workspace immediately.

Passive browsing never writes the campaign, creates an attempt, consumes quota
or alters evidence. The explicit generation action changes `currentTaskId`
only for an eligible object lane; simple navigation and prompt copying remain
read-only. The completion screen appears only after all sixteen tasks are
accepted, but the full archive remains navigable.

Use `-DryRun` to validate and prepare the campaign operator without starting
the server. Campaign data and result evidence stay under the durable campaign
directory; transient operator sessions stay under the chosen build output.

During development, modify and validate the active workflow in place. Rebuild
the manifest after verified changes, but do not reinstall or rebuild a release
ZIP during ordinary UI iterations. Packaging and staged reinstallation are
explicit release checkpoints only.

### Réviser un canon après des preuves humaines

Une preuve acceptée ne doit jamais être réécrite lorsqu'elle révèle une erreur
de direction artistique. La route autorisée est :

1. arrêter le Poste opérateur courant ;
2. figer dans la campagne les fichiers de canon exacts ayant produit ses
   preuves ;
3. corriger la source de canon et régénérer les canons ;
4. créer une nouvelle campagne versionnée ;
5. reporter seulement le préfixe d'états déjà acceptés et non affectés ;
6. déclarer les tâches acceptées mais invalidées comme `superseded` ;
7. reprendre au premier état qui doit être reconçu.

```powershell
.\scripts\art-direction.ps1 precanon-campaign-snapshot `
  -Campaign .\assets-3d\precanonical\campaigns\salvaged-frontier-states-v8\campaign.json

.\scripts\art-direction.ps1 canons

.\scripts\art-direction.ps1 precanon-campaign-fork `
  -SourceCampaign .\assets-3d\precanonical\campaigns\salvaged-frontier-states-v8\campaign.json `
  -Output .\assets-3d\precanonical\campaigns\salvaged-frontier-states-v9 `
  -CampaignId salvaged-frontier-states-v9 `
  -RestartTaskId 06-enemy-standard-intact `
  -RevisionReason "Les voies flexibles sont liées au compilateur final et le prompt exact est vérifié octet pour octet."
```

La campagne source passe à `BLOCKED`, son `currentTaskId` devient nul et tous
ses canons pointent vers des snapshots locaux hash-bound. La campagne révisée
enregistre le hash de la campagne source, la raison, les tâches reportées, les
tâches supplantées et le point exact de reprise. Les résultats, revues et images
restent à leur emplacement historique ; aucune copie ne change leur autorité.

## Legacy single-request operator route

For an isolated or already-existing historical request, run:

```powershell
.\scripts\art-direction.ps1 precanon-operator `
  -Request .\assets-3d\defense-barricade-small\precanonical\requests\defense-barricade-web-001\request.json `
  -Output .\tools\roblox-art-bible-sota-v3\build\precanonical\controlled-web-001\operator
```

This one command:

1. recomputes a current zero-consumption preflight;
2. composes one immutable submission text from the prompt and all negative
   constraints;
3. hashes the request, preflight, submission text and attachments;
4. reserves bounded result and review identities;
5. starts a token-bound HTTP server on `127.0.0.1` only;
6. opens the operator page in the default browser;
7. validates and imports the dropped image;
8. displays the imported image and records the review;
9. preserves normal result, provenance and authority contracts.

The human intervention is limited to:

- clicking **Copier le texte exact**;
- pasting it into an authenticated ChatGPT Web conversation;
- requesting exactly one generation;
- downloading exactly one image;
- dropping it into the operator page;
- choosing the review decision.

No Browser or Chrome plugin is required for this route. The page never reads
cookies, browser storage or credentials. It makes no API call and performs no
automatic retry. Its authentication token exists only in the URL fragment and
is not written into the operator manifest.

Use `-DryRun` to prepare and validate the operator session without starting the
server. Use `-NoOpen` when the operator URL should only be printed. The server
stops from the page or after the bounded idle timeout.

## Result provenance

The intake stores:

- request and prompt hashes;
- original image bytes;
- SHA-256, dimensions, format and byte count;
- generation index;
- download method;
- the conservative surface name `ChatGPT Web / ChatGPT Images`;
- an exact model name only when explicitly confirmed by the interface.

No image is overwritten. Duplicate image bytes are rejected.

## Review decisions

Allowed:

```text
REJECTED
REVISION_REQUIRED
PRECANONICAL_CANDIDATE
HUMAN_SELECTED
```

Forbidden:

```text
CANONICAL
PRODUCTION_APPROVED
```

Review covers functional conformity, art-direction conformity, visual
hierarchy, internal coherence and state coherence. Automation may support the
assessment, but only a named human may issue `HUMAN_SELECTED`.

## Relationship to the visual canon

The selected image is source material, not truth. Canonicalization must still
resolve:

- exact dimensions and proportions;
- rear, underside and hidden construction;
- stable components and names;
- pivots, axes, collision and interaction points;
- all states and transitions from one structure;
- invariants, tolerances, freedoms and prohibitions;
- technical and perceptual budgets;
- all required multimodal boards and human approval.

If a fact is not visible, strongly deducible or functionally decided, it
remains `UNKNOWN` or `HUMAN_ARBITRATION_REQUIRED`. It is never filled silently.
