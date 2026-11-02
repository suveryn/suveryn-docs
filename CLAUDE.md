# suveryn-docs

Public documentation for sūveryn, CC BY 4.0: the [manifesto](MANIFESTO.md), the [data lifecycle policy](administration/data-lifecycle.md), [Writing a playbook](playbooks/writing-a-playbook.md) (the manifest reference for offices and partners) and the [benchmarks](benchmarks/). The benchmark scripts are Apache-2.0.

For what sūveryn is and what is decided, start with the private [suveryn-handbook](https://github.com/suveryn/suveryn-handbook). Engineering detail lives in [suveryn-core/docs](https://github.com/suveryn/suveryn-core/tree/main/docs) and [suveryn-appliance/docs](https://github.com/suveryn/suveryn-appliance/tree/main/docs); this repository is what an office, a partner or a reviewer reads, not the engineering record.

## Rules

- **This repository is public.** Nothing commercial (pricing, the support model's internals, open business decisions), nothing about a client, no document content. If in doubt, it goes to the handbook.
- **The data lifecycle page governs every claim about deletion**, in the product, these docs and sales material. No claim of secure, permanent or cryptographic erasure anywhere; what is not covered is named.
- **Writing a playbook is kept in step with every core release that changes the manifest format**, in the same PR series. Its examples pass core's lint.
- **One branch and PR per change.** Merge only when the founder says so. Never change repository settings or CI.
- **Copy:** UK English, formal Dutch and French where translated, "sūveryn" lower case except at a sentence start or as the company, no em dashes, short. Markdown passes `markdownlint-cli2` (CI).
- **The manifesto changes only with the founder**, word by word.

## Verify

```bash
npx --yes markdownlint-cli2 "**/*.md"
```
