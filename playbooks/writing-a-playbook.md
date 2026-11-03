# Writing a playbook

A playbook is a routine sūveryn follows in a case: it asks for documents, reads them, asks about what it couldn't find, waits for a person to confirm every fact, and writes a result. You write a playbook as one YAML file, the **manifest**, plus its words in each language. This page is the reference for that file. It describes **manifest format 3** as sūveryn reads it today (format 2 plus lists and numbers; a format-2 file loads unchanged) and is kept up to date with every release that changes the format; the machine-readable version is the JSON Schema in [`suveryn-core/packages/playbooks/schema/`](https://github.com/suveryn/suveryn-core/tree/main/packages/playbooks/schema), which editors use for completion and checking.

Three rules shape everything below. The playbook decides the order of steps; the model only reads documents inside a `read` step and never chooses what comes next. A fact is never confirmed by the model: only a person does that, at a checkpoint. And the model answers in the shape the facts describe, no other: sūveryn derives that shape from the manifest and the model server holds the model to it, so a value is never taken by position or guessed from a stray line.

## A complete example

The official deed-intake playbook, as shipped (comments shortened):

```yaml
manifest: 3
id: playbook/be-notary/deed-intake
pack: pack/be-notary
version: "1.2"
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
  You are preparing the intake of a sale for a notarial deed. Read the excerpts and give every fact
  below as the documents write it … A fact the excerpts do not contain is null: never guess …
  Answer in the language of the documents.

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
| `manifest` | yes | The format version: `2` or `3`. Write `3`. Format 3 adds the kinds `number` and `list`; a format-2 file loads as it is, and a format-2 file that uses either kind is refused with the fact named. |
| `id` | yes | `playbook/<pack>/<name>`, lower case, digits and hyphens. Never changes once published: it ends up in every run's record, in every result document, and in the licence. |
| `pack` | yes | `pack/<profession-jurisdiction>`, for example `pack/be-notary`. The `id` must start with `playbook/<that pack>/`. |
| `version` | yes | `major.minor`, in quotes (`"1.1"`). A change that changes results is a new minor version; a change that makes an old run unreadable is a new major one. Every run records the version it ran under. |
| `name` | yes | The English name; it becomes the result document's file name ("Deed intake 2026/0417 (1.1).txt"). |
| `case_types` | yes | The case types the playbook fits, one or more: `sale`, `company-formation`, `estate`, `gift`, `marriage-contract` for notaries. It shows only in cases of those types. |
| `facts` | yes | What the playbook wants to know; see below. At most 100. |
| `instructions` | yes | What the model is told before it reads the documents, in English, up to 4 000 characters. Do **not** describe the answer's shape: sūveryn derives it from the facts and appends it. |
| `steps` | format 2 | The routine; see below. At most 50. |

Any key not listed here is an error. sūveryn refuses a file it doesn't fully understand rather than guess: every error names the file, the step or the field, and what is wrong.

## Facts

A fact is one thing the playbook needs to know. Each has:

| Key | Required | What it is |
|---|---|---|
| `id` | yes | Lower-case letters, digits and underscores, starting with a letter (`agreement_date`). Stable: labels, questions and the run's record key on it. |
| `ask` | yes | What the fact is, in the words the model gets, in English. Be concrete: "the date by which the notarial deed must be signed", not "deadline". |
| `kind` | no | `text` (default), `amount`, `date`, `number`, `choice` or `list`. Decides which checks apply to the value the model reads; `choice` says the value is one of a few options; `list` says the fact has several entries (below). |
| `of` | list only | What one entry is: a list of fields (each with `id`, `ask` and a plain `kind`), or one plain kind (`text`, `amount`, `date`, `number`) when each entry is a single value. |
| `options` | choice only | The option ids, two to twelve (`[cash, in_kind, mixed]`). Each has its words in the labels (`"contribution_kind.cash": "In cash"`). |

Every fact gets a label in each language in the words file (below); a list's fields too.

### Lists and numbers

A deed's parties don't fit one line. Format 3 lets a fact hold several entries:

```yaml
  - id: founders
    ask: the founders, one entry per founder
    kind: list
    of:
      - id: name
        ask: the founder's full name as written
      - id: shares
        ask: the number of shares this founder takes
        kind: number
      - id: contribution
        ask: this founder's contribution in money
        kind: amount
  - id: conditions
    ask: the conditions attached to the deed, one entry each
    kind: list
    of: text
```

The model gives one entry per founder the documents name, in the order the documents give them, and `[]` when they name none. Each value of an entry is a fact of its own, named by **path**: `founders[1].name`, `founders[2].contribution`, `conditions[1]`. Everything that works on a fact works on a path: the checks by kind, the checkpoint's card, a person's answer, the summary's line, the run's record. The list's own id (`founders`) names the list as a whole; it is what the playbook asks about when the documents name no entries ("The documents name no founders. Who are they?"), and the first entry a person gives answers it.

A list holds records of plain values, or plain values, never lists: a deed has several parties each with a few details and no deeper, and a file an office can still write by hand stays one level deep. At most 20 fields per entry and 50 entries per list.

`number` is a figure without currency: a count, a share, a percentage. It is checked by meaning against the cited passage like an amount, short figures included ("3 aandelen"), which the chat's own figure check leaves alone as too ambiguous; in a playbook you asked for a count, so it is checked.

People add entries. At a checkpoint, a list the documents named nothing of shows *Add* instead of *Fill in*, with one field per value of the entry; a list with entries offers one more under *More*. In words, "a third founder, Anna Peeters, 400 shares" adds one. Removing an entry is clearing its values.

### Choices, and steps that depend on them

A `choice` is a fact whose value is one of a few options:

```yaml
  - id: contribution_kind
    ask: "how the founders contribute: cash, in_kind or mixed"
    kind: choice
    options: [cash, in_kind, mixed]
```

The model reads it when the documents say it (it can only answer with an option); otherwise an `ask` step asks, and the thread offers the options as buttons. An answer in words ("in natura") is mapped to the option by its words in the run's language.

Any step may carry `when`, one condition on one choice: `when: contribution_kind != in_kind` or `when: contribution_kind == cash`. When the step is reached and the condition doesn't hold, or the choice isn't known by then, the step is skipped and the playbook says why in the thread, naming the step with its words from the words file (`steps.<step id>`): "Bank certificate: not needed, Contribution is In kind." A skipped `read` makes no facts, so nothing asks about them later; a skipped `check` has no result. The choice a `when` turns on must be read or asked by a step before it. No and/or, no conditions on other kinds of fact: the day a routine needs more, it needs a decision, not a longer line.

### What a fact does

A fact is the unit everything else works on. Over a run it goes through states, and every state is kept: nothing is overwritten, so a person can always see what the model read, what someone answered, and what was finally confirmed, and by whom.

1. **Proposed.** A `read` step found it in the documents. The value is copied as the documents write it, with the passage it came from. The `kind` decides the check sūveryn runs on it: an `amount`, `date` or `number` that isn't in the cited passage is flagged for the person to look at.
2. **Not established.** The documents didn't contain it. If an `ask` step covers it, the playbook asks a person; their answer becomes **proposed** too, marked as a person's, not the model's.
3. **Confirmed.** At the checkpoint a person confirms, corrects or clears every fact. Only this makes a fact the case's. A cleared fact stays **not established**, by that person.
4. **Superseded.** Every time a fact gets a new version, the old one is kept and marked superseded, pointing forward. A stopped run supersedes what it only read; a cancelled run supersedes everything it established, confirmed facts included. The rows stay, so the history is whole.

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

The playbook puts a question in the thread and waits until the case has the documents. If the case already has them when the step comes up, the step is done at once and no question is asked.

| Key | What it is |
|---|---|
| `min` | How many uploaded documents the case needs before the step is done. Default 1. |
| `allow_none` | `true` lets a person answer that there is no such document; the step is then skipped. Default `false`. |
| `expects` | A name for what is asked (`bank_certificate`), unique among the routine's requests, so a `read` can be aimed at it. When a person answers a named request, the documents that came with the answer are recorded as its; with none attached, the case's uploaded documents no other request has yet. |

The question's words come from the words file (`questions.<step id>`). After uploading, a person presses continue; sūveryn counts the case's uploaded documents.

### `read`: read the documents

The model reads the case's uploaded documents for the facts named and cites the passage each one came from. Facts it finds become **proposed**; facts the documents don't contain become **not established**. Never confirmed.

| Key | What it is |
|---|---|
| `facts` | Which facts to read: a list of ids, or `all`. Required. A fact is read by one `read` step; the loader refuses a second. |
| `documents` | The names (`expects`) of the requests whose documents this read reads: `[bank_certificate]`. Without it the read is over every document in the case. Aimed only at requests a person said have no document, the read makes no model call: its facts are not established, and an `ask` step can ask about them. |

Keep one `read` to about fifteen facts (a list counts as one); a routine with more needs several, each aimed at its own documents:

```yaml
steps:
  - id: bank
    kind: request
    expects: bank_certificate
    allow_none: true
  - id: bank_read
    kind: read
    documents: [bank_certificate]
    facts: [bank_certificate, certified_amount]
``` A `read` step is one grounded model call whose answer must have the facts' shape; the model server enforces that shape, and an answer that still can't be read is asked for once more, then the run fails as "unreadable answer" and can be started again.

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

### `check`: what the notary would add up

The server computes one comparison on the values as they stand and shows the result at the checkpoint and in the summary. A failed check is a point for the notary, never a block; the model never does arithmetic.

| Key | What it is |
|---|---|
| `rule` | One comparison: `sum(founders.shares) == shares`, `certified_amount == contribution`, `count(founders) >= 1`, `plan_date <= deed_date`. A side is a fact, the sum of a list's field, the count of a list's entries, or a number; both sides are of one kind (amount, number or date). Operators: `==`, `!=`, `<`, `<=`, `>`, `>=`. Nothing else: no arithmetic, no and/or, no text. |

```yaml
  - id: shares_add_up
    kind: check
    rule: sum(founders.shares) == shares
```

A result **holds**, **fails** (both sides as computed, so the notary sees 1050 against 1000) or is **open** when a value it needs is missing or gives no amount, number or date as written; it is recomputed whenever a value changes. A check comes after the read or ask steps that supply its facts. Its sentence per language is in the words file (`checks.<step id>`: "The founders' shares add up to the shares issued"); the file refuses a check without one.

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

`labels` needs an entry for every fact and, for a list, for every field as `"<list id>.<field id>"` (`"founders.name": "Name"`); an entry's values are labelled from these: "Founder(s) 2 · Name". A choice's options have theirs as `"<fact id>.<option>"`. `checks` needs a sentence per `check` step, what holds when it holds. `steps` names steps for the line that says one was skipped (`"bank": "Bank certificate"`); a step without a name is called by its id. `questions` needs an entry for every `request` step and every `ask` step (a template with `{label}`, or one entry per fact as `"missing.price": "…"`; for a list, `"missing.founders"` is asked when the documents name no entries). The model never words a question: what people read is what you wrote.

## What happens when it runs

A run is a conversation with the routine. The playbook asks; people answer, in the case, in the run's language. The case shows that a playbook is running and what it waits for. A run can be paused and resumed by anyone who contributes to the case; stopped (what was confirmed stays, what was only read is dropped) or cancelled (nothing the run established counts any more, confirmed or not, and its result is marked withdrawn) by whoever started it or the case manager. Every fact keeps every version it had (as read, as answered, as confirmed, and by whom), and nothing is rewritten. One run of a playbook at a time per case.

## Checking a file

The loader refuses a wrong file with the place and the reason, for example:

```text
be_notary/mandate.yaml: 2 problem(s):
  steps: step 'summary' (produce): nothing is produced before a checkpoint; it needs one
  facts.3.kind: Input should be 'text', 'amount' or 'date'
```

Editors that understand JSON Schema (VS Code with the YAML extension, among others) check as you type when pointed at the schema file.

## What is not in the format yet

Checks on documents that disagree, conditions on anything but a choice, who may pass a checkpoint by role, documents from the office's own templates, and lists inside lists (on purpose: see Lists and numbers). They arrive in later formats; a format-2 or format-3 file keeps loading as it is.
