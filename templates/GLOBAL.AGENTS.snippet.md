<!-- BEGIN gabrielrojasc/skills -->
## Tracker and implementation workspace

- Linear is the default issue tracker unless a repository states otherwise. Linear owns active scope, dependencies, ownership, and progress. Git owns code, branches, worktrees, and commits.
- Fetching Linear data is read-only. Get explicit human approval before creating or updating Linear issues, projects, comments, or workflow state.
- Repository containers live under `<REPOS_ROOT>/<repo>/`. The persistent default-branch worktree lives at `<REPOS_ROOT>/<repo>/<default-branch>/` and is used for browsing and synchronization.
- Before implementation, use `$git-workspace` to create or select an isolated task worktree. An explicit user instruction to use the current checkout overrides this default.
- Keep stable technical knowledge in repository documentation and ADRs. Do not mirror active Linear state into planning files.
<!-- END gabrielrojasc/skills -->
