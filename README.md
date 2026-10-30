# Sūveryn documentation

Website: [suveryn.com](https://www.suveryn.com)

Installation, administration, playbook-writing and connector-development documentation for sūveryn.

Related repositories:

- [suveryn-core](https://github.com/suveryn/suveryn-core): the engine, chat, document pipeline, API gateway and chat UI (AGPL-3.0-or-later). Its [architecture document](https://github.com/suveryn/suveryn-core/blob/main/docs/architecture.md) is the starting point for code reviewers.
- [suveryn-appliance](https://github.com/suveryn/suveryn-appliance): the OS image and runtime services (PostgreSQL, Keycloak, the model server).
- [suveryn-brand](https://github.com/suveryn/suveryn-brand): the mark, fonts, design tokens and brand guidelines.
- [suveryn-connector-sdk](https://github.com/suveryn/suveryn-connector-sdk) and [suveryn-connectors-registry](https://github.com/suveryn/suveryn-connectors-registry): building and listing connectors.

## Contents

- [Data lifecycle](administration/data-lifecycle.md): what sūveryn keeps, for how long, and what deleting guarantees. The policy every claim about deletion follows.
- [Writing a playbook](playbooks/writing-a-playbook.md): the manifest file, step by step, for offices and partners that write their own routines. Kept in step with every release that changes the format.
- [Benchmarks](benchmarks/): hardware and pipeline measurements for development pods and on-prem appliances.

## Licence

The documentation in this repository is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the full text is in [LICENSE](LICENSE).

The code is not: the benchmark scripts in [`benchmarks/scripts/`](benchmarks/scripts/) are licensed under Apache-2.0 ([their LICENSE](benchmarks/scripts/LICENSE)), as Creative Commons advises against its licences for software.
