# suveryn-docs

Public documentation for sūveryn, CC BY 4.0: the [manifesto](MANIFESTO.md), the [data lifecycle policy](administration/data-lifecycle.md), [Writing a playbook](playbooks/writing-a-playbook.md) (the manifest reference for offices and partners) and the [benchmarks](benchmarks/). The benchmark scripts are Apache-2.0.

For what sūveryn is and what is decided, start with the private [suveryn-handbook](https://github.com/suveryn/suveryn-handbook/blob/main/context/development-context.md#start-here), its *Start here*: the design principles, the project's words, and how a change reaches `main`. Engineering detail lives in [suveryn-core/docs](https://github.com/suveryn/suveryn-core/tree/main/docs) and [suveryn-appliance/docs](https://github.com/suveryn/suveryn-appliance/tree/main/docs); this repository is what an office, a partner or a reviewer reads, not the engineering record.

## Rules

- **This repository is public.** Nothing commercial (pricing, the support model's internals, open business decisions), nothing about a client, no document content. If in doubt, it goes to the handbook.
- **The data lifecycle page governs every claim about deletion**, in the product, these docs and sales material. No claim of secure, permanent or cryptographic erasure anywhere; what is not covered is named.
- **Writing a playbook is kept in step with every core release that changes the manifest format**, in the same PR series. Its examples pass core's lint.
- **One branch and PR per change.** Merge only when the founder says so. Never change repository settings or CI. A coding agent never pushes: it delivers a patch, applied in a separate worktree, as *Start here* says.
- **Written for someone who doesn't know the code**: an office, a partner, a reviewer. Short and plain: what it does and why. **Copy** follows the brand's [Wording and spelling](https://github.com/suveryn/suveryn-brand/blob/main/guidelines/brand-guidelines.md#wording-and-spelling). Markdown passes `markdownlint-cli2` and the link check (CI). Links to private repositories (the handbook) are listed in `.markdown-link-check.json` `ignorePatterns`, since a private repository answers 404 to the checker.
- **The manifesto changes only with the founder**, word by word.

## Verify

```bash
npx --yes markdownlint-cli2 "**/*.md"
npx --yes markdown-link-check --config .markdown-link-check.json CLAUDE.md   # or any changed file
```
