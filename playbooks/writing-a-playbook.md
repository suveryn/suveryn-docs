# Writing a playbook

A playbook is a routine sūveryn follows in a case: it asks for documents, reads them, asks about what it couldn't find, waits for a person to confirm every fact, and writes a result. You write a playbook as one YAML file, the **manifest**, plus its words in each language. This page is the reference for that file. It describes **manifest format 2** as sūveryn reads it today and is kept up to date with every release that changes the format; the machine-readable version is the JSON Schema in [`suveryn-core/packages/playbooks/schema/`](https://github.com/suveryn/suveryn-core/tree/main/packages/playbooks/schema), which editors use for completion and checking.

Two rules shape everything below. The playbook decides the order of steps; the model only reads documents inside a `read` step and never chooses what comes next. And a fact is never confirmed by the model: only a person does that, at a checkpoint.

## A complete example

The official deed-intake playbook, as shipped (comments shortened):

```yaml
manifest: 2
id: playbook/be-notary/deed-intake
pack: pack/be-notary
version: "1.1"
name: Deed intake
case_types: [sale]

facts:
  - id: sellers
    ask: the selling party or parties, as named in the agreement (full names as written)
  - id: price
    ask: the sale price
    kind: amount
  - id: agreement_date
    ask: the date the private agreement was signed
    kind: date
  # … eleven more

instructions: >-
  You are preparing the intake of a sale for a notarial deed. Read the excerpts and fill in the
  table below … Answer with the table only, in the language of the documents.

steps:
  - id: agreement
    kind: request
    min: 1
  - id: read
    kind: read
    facts: all
  - id: missing
    kind: ask
    facts: all
  - id: confirm
    kind: checkpoint
    by: anyone_in_case
  - id: summary
    kind: produce
    template: summary
```

Read it top to bottom: who the playbook is (`id`, `pack`, `version`), where it fits (`case_types`), what it wants to know (`facts`), what it tells the model (`instructions`), and what it does, in order (`steps`).

## The file

| Key | Required | What it is |
|---|---|---|
| `manifest` | yes | The format version: `1` or `2`. Write `2`. A format-1 file has no `steps` and runs as read → checkpoint → produce. |
| `id` | yes | `playbook/<pack>/<name>`, lower case, digits and hyphens. Never changes once published: it ends up in every run's record, in every result document, and in the licence. |
| `pack` | yes | `pack/<profession-jurisdiction>`, for example `pack/be-notary`. The `id` must start with `playbook/<that pack>/`. |
| `version` | yes | `major.minor`, in quotes (`"1.1"`). A change that changes results is a new minor version; a change that makes an old run unreadable is a new major one. Every run records the version it ran under. |
| `name` | yes | The English name; it becomes the result document's file name ("Deed intake 2026/0417 (1.1).txt"). |
| `case_types` | yes | The case types the playbook fits, one or more: `sale`, `company-formation`, `estate`, `gift`, `marriage-contract` for notaries. It shows only in cases of those types. |
| `facts` | yes | What the playbook wants to know; see below. At most 100. |
| `instructions` | yes | What the model is told before it reads the documents, in English, up to 4 000 characters. Do **not** write the answer table: sūveryn appends it. |
| `steps` | format 2 | The routine; see below. At most 50. |

Any key not listed here is an error. sūveryn refuses a file it doesn't fully understand rather than guess: every error names the file, the step or the field, and what is wrong.

## Facts

A fact is one thing the playbook needs to know. Each has:

| Key | Required | What it is |
|---|---|---|
| `id` | yes | Lower-case letters, digits and underscores, starting with a letter (`agreement_date`). Stable: labels, questions and the run's record key on it. |
| `ask` | yes | What the fact is, in the words the model gets, in English. Be concrete: "the date by which the notarial deed must be signed", not "deadline". |
| `kind` | no | `text` (default), `amount` or `date`. Decides which checks apply to the value the model reads. |

Every fact gets a label in each language in the words file (below). Today a fact is one value; lists of records (several founders, each with name, shares and contribution) and typed numbers are the next format.

### What a fact does

A fact is the unit everything else works on. Over a run it goes through states, and every state is kept: nothing is overwritten, so a person can always see what the model read, what someone answered, and what was finally confirmed, and by whom.

1. **Proposed.** A `read` step found it in the documents. The value is copied as the documents write it, with the passage it came from. The `kind` decides the check sūveryn runs on it: an `amount` or `date` that isn't in the cited passage is flagged for the person to look at.
2. **Not established.** The documents didn't contain it. If an `ask` step covers it, the playbook asks a person; their answer becomes **proposed** too, marked as a person's, not the model's.
3. **Confirmed.** At the checkpoint a person confirms, corrects or clears every fact. Only this makes a fact the case's. A cleared fact stays **not established**, by that person.
4. **Superseded.** Every time a fact gets a new version, the old one is kept and marked superseded, pointing forward. If a run is cancelled, its confirmed facts go back to proposed the same way, so the history stays whole.

Where a fact shows: in the thread, when the playbook asks about it; at the checkpoint, beside its passage, with the check's warning; in the panel next to the thread, with its state; in the summary, as one line with its sources. When a document a fact was read from is later deleted, the run is marked out of date, but the fact and its passage stay.

Writing a good `ask`: name the thing exactly as a careful clerk would ("the date by which the notarial deed must be signed"), say what form you want ("full names as written"), and keep one fact per line of the deed. If a value can't be checked by a person at a glance, split it into two facts.

### The deed-intake facts, as an example

| Fact | Kind | Why it is there |
|---|---|---|
| `sellers`, `buyers` | text | The parties, as the agreement names them; the deed must match the agreement exactly |
| `property` | text | Address and description, for the deed's description of the good |
| `cadastral` | text | Municipality, division, section, number; often missing from the agreement, hence usually asked |
| `price` | amount | The check compares it with the cited passage |
| `deposit` | amount | What was paid at signing and to whom, for the settlement |
| `agreement_date` | date | Starts the deadlines |
| `deed_deadline` | date | By when the deed must be passed |
| `conditions` | text | Suspensive conditions with their terms, which decide whether the sale stands |
| `title` | text | The seller's earlier deed: its date and notary, for the chain of title |
| `epc`, `soil` | text | The energy and soil certificates' references and conclusions, which the deed must cite |
| `occupancy` | text | Free, let or occupied, and by whom, at delivery |

Thirteen, not more: every fact is a line the notary has to check, and a checkpoint with forty lines is one nobody reads.

## Steps

A step is one thing the routine does. Steps run in the order they can: a step starts when every step it `needs` is done. By default a step needs the one before it, so a plain list runs top to bottom.

Every step has an `id` (lower case, digits, hyphens or underscores) and a `kind`. The other keys depend on the kind; a key that belongs to another kind is an error.

### `request`: ask for documents

The playbook puts a question in the thread and waits until the case has the documents.

| Key | What it is |
|---|---|
| `min` | How many uploaded documents the case needs before the step is done. Default 1. |
| `allow_none` | `true` lets a person answer that there is no such document; the step is then skipped. Default `false`. |

The question's words come from the words file (`questions.<step id>`). After uploading, a person presses continue; sūveryn counts the case's uploaded documents.

### `read`: read the documents

The model reads the case's uploaded documents for the facts named and cites the passage each one came from. Facts it finds become **proposed**; facts the documents don't contain become **not established**. Never confirmed.

| Key | What it is |
|---|---|
| `facts` | Which facts to read: a list of ids, or `all`. Required. |

Keep one `read` to about fifteen facts; a routine with more needs several. A `read` step is one grounded model call; an answer that isn't the table is asked for once more, then the run fails as "unreadable answer" and can be started again.

### `ask`: ask people about what wasn't found

For every fact in `facts` that the documents didn't contain, the playbook puts one question in the thread. A person answers what they know; an empty answer means "not known yet". Answers become **proposed** facts from a person, still to be confirmed.

| Key | What it is |
|---|---|
| `facts` | Which facts to ask about if missing: a list of ids, or `all`. Required. Only facts a `read` step before this one reads. |

The words come from `questions.<step id>` (a template with `{label}`) or `questions.<step id>.<fact id>` for one fact's own question. If nothing is missing, the step is skipped.

### `checkpoint`: a person confirms

The run waits. A person sees every fact beside the passage it was read from, with the check's warning where a figure, date or name isn't in the cited passage, and confirms, corrects or clears each one. Only then are facts **confirmed**.

| Key | What it is |
|---|---|
| `by` | Who may pass it. Only `anyone_in_case` today (anyone who contributes to the case). |

A routine must have a checkpoint, after a `read` or `ask` step and before any `produce`.

### `produce`: write the result

Writes the confirmed facts into the case as a document, named after the playbook, the case and the run's version, in the language the run was started in. It is never used as a source for answers.

| Key | What it is |
|---|---|
| `template` | Only `summary` today: a heading, one line per fact with its sources. Documents from the office's own templates are a later format. |

### `needs`

Any step may name the steps that must be done first: `needs: [read, missing]`. Default: the step before it. The graph is checked when the file loads: every id once, every `needs` a real step, no circle, a checkpoint before any `produce`, an `ask` only about facts a `read` before it reads.

## The words file

Beside the manifest, one JSON file per language in `text/` (`en.json`, `nl.json`, `fr.json`; every language is required). Under the playbook's slug (the last part of its id):

```json
{
  "deed-intake": {
    "title": "Deed intake",
    "summary": "Reads the facts for the deed from the documents",
    "labels": { "sellers": "Seller(s)", "price": "Price", "agreement_date": "Agreement signed on" },
    "questions": {
      "agreement": "Upload the signed sale agreement and what the parties sent. Then continue.",
      "missing": "The documents don't mention {label}. What is it? Leave empty if you don't know yet."
    }
  }
}
```

`labels` needs an entry for every fact. `questions` needs an entry for every `request` step and every `ask` step (a template with `{label}`, or one entry per fact as `"missing.price": "…"`). The model never words a question: what people read is what you wrote.

## What happens when it runs

A run is a conversation with the routine. The playbook asks; people answer, in the case, in the run's language. The case shows that a playbook is running and what it waits for. A run can be paused and resumed by anyone who contributes to the case; stopped (what was confirmed stays, what was only read is dropped) or cancelled (confirmed facts go back to unconfirmed, the result is marked withdrawn) by whoever started it or the case manager. Every fact keeps every version it had — as read, as answered, as confirmed, by whom — and nothing is rewritten. One run of a playbook at a time per case.

## Checking a file

The loader refuses a wrong file with the place and the reason, for example:

```text
be_notary/mandate.yaml: 2 problem(s):
  steps: step 'summary' (produce): nothing is produced before a checkpoint; it needs one
  facts.3.kind: Input should be 'text', 'amount' or 'date'
```

Editors that understand JSON Schema (VS Code with the YAML extension, among others) check as you type when pointed at the schema file.

## What is not in the format yet

Decisions and conditions (`when`), named document requests, repeating a block per founder, checks on sums and on documents that disagree, who may pass a checkpoint by role, documents from the office's own templates, and facts that are lists or numbers. They arrive in later formats; a format-2 file keeps loading as it is.
