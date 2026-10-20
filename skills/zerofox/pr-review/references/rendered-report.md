# Rendered report

Show one PR's triage report as a page with the HTML render tool, built from the
template below. The page holds every item Triage step 3 lists; the chat reply
holds only the question from step 4, or the stop on the user's own PR.

## Fill the template

Keep the `<style>` block unchanged and fill the body top to bottom:

1. **Headline.** The event as `Request changes` (class `bad`), `Comment` (no
   class), or `Approve` (class `ok`), then the repository and number linked to
   the PR.
2. **Reason.** One sentence on why the review carries that event. On the third
   or later review that still has blockers, add a second sentence suggesting a
   call or a rethink of the approach.
3. **Meta line.** The Risk level when the Risk agent ran, the CI state with the
   short head SHA (class `ok` when passing, `bad` when failing), and
   `Not posted`, or `Your PR, nothing posts` on the user's own PR.
4. **Needs your call.** One `.f` per raised finding: ID, severity, the
   `file-links.sh` link, the problem, why it matters, and the full draft. A
   `wording unsettled` finding adds `Wording unsettled` after its severity and
   a `<p>` starting `Wording:` with the sticking point. A raised +1 links the
   bot's comment and quotes it in place of the draft.
5. **Approach.** Each Approach alternative in one `<p>`.
6. **Earlier threads.** On a re-review, one `<p>` per thread: its link and
   `addressed`, `unaddressed`, or `author replied`.
7. **Posts as is.** One `.f` per routine finding with ID, severity, link, and
   full draft. A routine +1 links the bot's comment and says why it holds.
8. **Notes.** Each note about direction or a new pattern others will copy, one
   `<p>` each.
9. **Context.** Inside `<details>`: the three-line summary of what the change
   does, the Risk reasons, what the author tested, what the review didn't
   check, the counts of refuted and dropped drafts and of other notes, and the
   path to `triage.md`.

Drop a `.group` that has no items. HTML-escape every draft, quote, and path so
backticks and angle brackets show as written.

## Show it

Call the preview tool with the page to get its content height, fix what the
screenshot shows broken, then call the render tool with that height and the
title `Review: <repo>#<n>`. Write no restatement of the page in the reply.

## Template

```html
<!doctype html>
<html><head><meta charset="utf-8">
<style>
  *{box-sizing:border-box}
  body{font-family:var(--font-sans);color:var(--foreground);font-size:14px;line-height:1.5}
  ::selection{background:var(--accent-surface);color:var(--accent-surface-foreground)}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline;text-underline-offset:2px}
  a:focus-visible,summary:focus-visible{outline:2px solid var(--ring);outline-offset:2px;border-radius:4px}
  .mono{font-family:var(--font-mono);font-size:12.5px}
  .muted{color:var(--muted-foreground)}
  .bad{color:var(--destructive)}
  .ok{color:var(--success)}
  .verdict{font-size:18px;font-weight:600;margin:0;letter-spacing:-.01em}
  .verdict a{color:var(--foreground)}
  .sub{margin:4px 0 0;max-width:68ch}
  .meta{margin:6px 0 0;font-size:13px;color:var(--muted-foreground)}
  .meta span+span::before{content:"·";margin:0 8px;color:var(--border)}
  .group{margin-top:22px}
  .group-h{font-size:13px;font-weight:600;margin:0 0 8px}
  .group>p:not(.group-h){margin:4px 0 0;max-width:68ch}
  .f{margin:0 0 16px}
  .f-line{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
  .id{font-weight:600}
  .sev{font-size:12.5px;font-weight:600}
  .f p{margin:4px 0 0;max-width:68ch}
  .draft{margin:8px 0 0;padding:10px 12px;background:var(--muted);border-radius:8px;max-width:68ch;overflow-wrap:anywhere}
  details{margin-top:20px;font-size:13px}
  summary{cursor:pointer;color:var(--muted-foreground)}
  details>div{margin-top:8px;color:var(--muted-foreground);max-width:68ch}
  details p{margin:4px 0}
  @media (max-width:520px){.f-line{gap:6px}}
</style></head><body>

<p class="verdict"><span class="bad">Request changes</span> on <a href="https://github.com/OWNER/REPO/pull/N">REPO #N</a></p>
<p class="sub">EVENT_REASON</p>
<p class="meta"><span>Risk LEVEL</span><span class="ok">CI passing at <span class="mono">SHORT_SHA</span></span><span>Not posted</span></p>

<div class="group">
  <p class="group-h">Needs your call</p>
  <div class="f">
    <div class="f-line"><span class="id">S1</span><span class="sev bad">Blocking</span><a class="mono" href="FILE_LINK">PATH:LINE</a></div>
    <p>PROBLEM</p>
    <p class="muted">WHY_IT_MATTERS</p>
    <div class="draft">DRAFT</div>
  </div>
</div>

<div class="group">
  <p class="group-h">Approach</p>
  <p>ALTERNATIVE</p>
</div>

<div class="group">
  <p class="group-h">Earlier threads</p>
  <p><a href="THREAD_LINK">THREAD_NAME</a> <span class="muted">STATUS</span></p>
</div>

<div class="group">
  <p class="group-h">Posts as is</p>
  <div class="f">
    <div class="f-line"><span class="id">N1</span><span class="sev muted">Nitpick</span><a class="mono" href="FILE_LINK">PATH:LINE</a></div>
    <div class="draft">DRAFT</div>
  </div>
</div>

<div class="group">
  <p class="group-h">Notes</p>
  <p>DIRECTION_NOTE</p>
</div>

<details><summary>Context: what changed, evidence, N_REFUTED refuted</summary><div>
  <p>SUMMARY</p>
  <p>RISK_REASONS</p>
  <p>Author tested: TESTED. Not checked: UNCHECKED.</p>
  <p>N_REFUTED refuted, N_DROPPED dropped, N_NOTES notes in <span class="mono">TRIAGE_PATH</span></p>
</div></details>

</body></html>
```
