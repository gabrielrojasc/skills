# Rendered header

Show one PR's verdict as a small page with the HTML render tool, titled
`Review: <repo>#<n>`, then write the rest of the report in Markdown below it.
Fill the template:

1. **Headline.** The event as `Request changes` (class `bad`), `Comment` (no
   class), or `Approve` (class `ok`), then the repository and number linked to
   the PR.
2. **Reason.** One sentence on why the review carries that event.
3. **Meta line.** The risk level, the CI state with the short head SHA (class
   `ok` when passing, `bad` when failing), and `Not posted`, or
   `Your PR, nothing posts` on the user's own PR.

HTML-escape every value.

```html
<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body{font-family:var(--font-sans);color:var(--foreground);font-size:14px;line-height:1.5}
  a{color:var(--accent);text-decoration:none}
  .mono{font-family:var(--font-mono);font-size:12.5px}
  .bad{color:var(--destructive)}
  .ok{color:var(--success)}
  .verdict{font-size:18px;font-weight:600;margin:0;letter-spacing:-.01em}
  .verdict a{color:var(--foreground)}
  .sub{margin:4px 0 0;max-width:68ch}
  .meta{margin:6px 0 0;font-size:13px;color:var(--muted-foreground)}
  .meta span+span::before{content:"·";margin:0 8px;color:var(--border)}
</style></head><body>
<p class="verdict"><span class="bad">Request changes</span> on <a href="https://github.com/OWNER/REPO/pull/N">REPO #N</a></p>
<p class="sub">EVENT_REASON</p>
<p class="meta"><span>Risk LEVEL</span><span class="ok">CI passing at <span class="mono">SHORT_SHA</span></span><span>Not posted</span></p>
</body></html>
```
