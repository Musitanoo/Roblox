# Precanonical Web visualization

Use this reference when an asset needs visual exploration before its canonical
definition is complete.

## Authority

- ChatGPT Web Images is replaceable visualization transport.
- Its images are never geometry or canon authority.
- The selected Salvaged Frontier constitution must be hash-bound.
- Human selection authorizes canonicalization only.
- `productionApproved` remains false.

## Local sequence

For the selected six-object corpus, use the persistent state campaign:

~~~powershell
.\scripts\art-direction.ps1 precanon-campaign-init -Output <campaign-dir>
.\scripts\art-direction.ps1 precanon-campaign-operator -Campaign <campaign.json> -Output <operator-runtime>
~~~

This route is authoritative for state-image collection. It contains exactly
six objects and sixteen applicable object-state tasks. Each task requires one
visibly confirmed `gpt-image-2` generation and one downloaded image. Never
combine multiple gameplay states in one primary generation.

The first state of each object derives from its exact canon. Every later state
must attach the accepted previous state of the same object and preserve its
construction, footprint, components, anchors, material identity and
recognition landmarks. An accepted review advances immediately. A revision or
rejection creates a bounded explicit attempt on the same task; it is never an
automatic retry.

For isolated exploration or historical evidence, the legacy request sequence
remains available:

~~~powershell
.\scripts\art-direction.ps1 precanon-init -Brief <brief> -RequestId <id> -Output <request-dir>
.\scripts\art-direction.ps1 precanon-preflight -Request <request.json> -Output <preflight.json>
.\scripts\art-direction.ps1 precanon-browser-doctor -BrowserAdapter <codex_iab|codex_chrome> -Output <browser-doctor.json>
.\scripts\art-direction.ps1 precanon-handoff -Request <request.json> -Preflight <preflight.json> -BrowserDoctor <browser-doctor.json> -Output <handoff.json>
.\scripts\art-direction.ps1 precanon-operator -Request <request.json> -Output <operator-dir>
~~~

Do not touch the browser unless the preflight is `PASS` and the user has
authorized the bounded generation. The local Browser doctor must also report
`localInstallationStatus=PASS`. The handoff remains
`AWAITING_TASK_BROWSER_CAPABILITY` with `submissionAuthorized=false` until the
current task visibly exposes `mcp__node_repl__js`.

When that task capability is absent, `precanon-campaign-operator` is the
supported semi-automatic route for the selected corpus; `precanon-operator`
is reserved for one standalone request. Both rerun and bind preflight
themselves and therefore do not require a Browser doctor or handoff. They open
a loopback-only interface
where the human:

1. copies one exact text containing the prompt and all bound negatives;
2. opens ChatGPT Web and submits it without rewriting;
3. requests and downloads exactly one result;
4. drops that image into the local page;
5. records the bounded review.

The campaign interface also displays every object and state, progress,
continuity references, attempt counts, recorded previews and the next task.
Every state remains selectable before generation. The explorer exposes
filters, previous/next navigation, deep links, status explanations,
continuity dependencies and every imported attempt without changing the
campaign's active task. Rejected and revision-required images remain
consultable as evidence; a pending state displays an explicit placeholder
rather than a disabled control.
Global object order is not a generation gate. The first state of every object
is an independent eligible lane and the operator may explicitly activate any
eligible lane. Object-local continuity remains mandatory: a later state becomes
generation-eligible only after the previous state of that same object is
accepted. Its canonical prompt remains readable and copyable beforehand as a
clearly labelled preview; the exact hash-bound transport prompt is created only
when the continuity reference exists.
It automatically validates bytes, dimensions, format, budget, duplicates,
hashes, provenance, result identity and review authority. It does not read
browser state, use an API, retry, or automate submission.

For accepted reviews, the operator pre-fills the preserve field from the exact
state invariants in the bound source brief. Later states and correction
attempts also inherit explicit preserve rules from their reviewed continuity
result. These suggestions remain editable and require human confirmation; the
operator must never auto-pass the five perceptual assessment dimensions or
overwrite human edits during ordinary navigation. Reviewer identity is enabled
only for `HUMAN_SELECTED`.

During normal development, patch and validate the active workflow in place.
Do not repeatedly uninstall or reinstall it. Rebuild a release archive and run
the staged installer only at an explicit release checkpoint or when bootstrap,
dependency or installation behavior itself changed.

Use the exact `browserAdapter` selected by the request:

- `codex_iab` is permitted only when the handoff has zero attachments;
- `codex_chrome` is required when any hash-bound reference must be uploaded;
- never switch adapters automatically.

## Codex browser runtime hygiene

The Browser and Chrome plugins own their control runtime. Codex may legitimately
generate and refresh `mcp_servers.node_repl`, `NODE_REPL_*`, `BROWSER_USE_*`
and native-pipe values in `~/.codex/config.toml`. Treat those entries as
app-managed state:

- never delete them merely because a feature flag is marked removed;
- never copy them from another machine, app build or task;
- never hand-edit pipe identifiers or trusted hashes;
- never use their presence as proof that the current task exposes the MCP tool.

Keep transport readiness separate from the deterministic precanonical
preflight. A request may be `PASS` and still be externally `BLOCKED` because
the current task does not expose Browser control.

After changing plugin or browser configuration, restart the ChatGPT/Codex
desktop app and start a fresh task before attempting submission. A task created
before the change must not be treated as proof that the repair failed.

For Chrome, if the official native-host diagnostic fails, reinstall the Chrome
plugin through the ChatGPT plugin UI. Do not repair the registry or native host
with repository scripts.

If `node_repl` itself exposes `js` but the task capability manifest omits
`mcp__node_repl__js`, stop with `WEB_TASK_CAPABILITY_UNAVAILABLE`. Repository
scripts must not invoke the MCP server directly as a hidden browser-control
proxy. Offer the explicit `precanon-operator` route instead.

For either adapter:

1. reuse one authenticated tab;
2. submit the exact handoff prompt;
3. attach only bound files when using `codex_chrome`; assert zero attachments
   when using `codex_iab`;
4. request one result;
5. download once;
6. analyze the local file.

Never inspect authentication data, silently retry, infer an invisible quota,
rewrite the prompt in the browser, or fall back to imagegen/API.

Import and review:

~~~powershell
.\scripts\art-direction.ps1 precanon-import -Request <request.json> -ResultId <id> -Image <png> -Output <result-dir>
.\scripts\art-direction.ps1 precanon-review -Result <result.json> -RequestId <review-id> -ReviewDecision <decision> -Output <review.json>
~~~

Allowed decisions are `REJECTED`, `REVISION_REQUIRED`,
`PRECANONICAL_CANDIDATE`, and `HUMAN_SELECTED`. `CANONICAL` is deliberately
impossible. A named human and five passing assessment dimensions are required
for `HUMAN_SELECTED`.

Create a new correction request rather than regenerating a successful prompt.
Bind the previous result and express observable preserve/correct/forbid rules.
