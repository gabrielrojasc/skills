# Global agent guidance

The repository owns one short section for the user-level `AGENTS.md`. Its purpose is to define the Linear and Git ownership boundary and route implementation into `$git-workspace`.

The canonical template is [`templates/GLOBAL.AGENTS.snippet.md`](../templates/GLOBAL.AGENTS.snippet.md). Print it with:

```bash
scripts/render-global-agents-snippet.sh
```

Use `--repos-root` when repository containers do not live under `~/git`.

The renderer writes only to stdout. Review and merge its output into the user-level file manually or through a separately approved edit. The bounded comments make the section easy to replace later.

Matt Pocock's model-invoked skills rely on automatic discovery. User-invoked skills run only when the user names them. This template does not duplicate their workflow. It records only local policy that those skills cannot infer, especially Linear ownership, approval before tracker writes, and the workspace layout.
