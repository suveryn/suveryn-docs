# Data lifecycle: what sūveryn keeps, for how long, and what deleting guarantees

This page is the policy. Everything sūveryn says about deletion, in the product, in its documentation and in sales material, follows it. It was decided on 17 October 2026 (suveryn-tracker#31) and changes only with a new decision recorded here.

The one-paragraph version: **deleting something in sūveryn removes it from sūveryn at once, for everyone, and it cannot be found, searched, cited or shown again. Traces of it in the database's files are overwritten over time, in the ordinary course of the database's housekeeping. The appliance's data disk is encrypted, so those traces are unreadable off the machine. Backups, once they exist, expire after their retention period, and a deleted item lives on in a backup only until that backup does.** Sūveryn does not claim secure or cryptographic erasure, because it has not built it. The reasoning is at the end.

## What sūveryn keeps

Everything an office puts into sūveryn lives on the appliance, in one PostgreSQL database and one work folder, on the encrypted data partition. Nothing is sent anywhere else. In short:

| What | Where | Kept |
|---|---|---|
| Documents: the file name, a hash, the text read from them (as passages with their page), the search index over that text | Database (`documents`, `chunks`) | Until the document is deleted, or until the case it is in is deleted |
| Uploaded files themselves | Work folder, only while a document is being read | Minutes: deleted as soon as the document has been read, also on failure; leftovers of a crash are deleted at the next start |
| Cases: the file number, name, type, a short subject, members and their roles, state | Database (`cases`, `case_members`) | Open cases until someone deletes them; closed cases for the office's keep period (6 months, 1 year, 5 years, or until deleted by hand), then deleted with everything in them |
| The access log of a case: who did what and when, with ids only, never text | Database (`case_events`) | 180 days, then deleted; with the case when the case is deleted |
| Saved conversations: questions, answers, the passages they cite, attachment names | Database (`conversations`) | Until their owner deletes them, until the case they are in is deleted, or until the office's conversation keep period passes (below) |
| Usage: per model call, who, when, which model, how many tokens; no text | Database (`token_usage`) | Indefinitely; it contains no content |
| Accounts, password hashes, second factors, sessions | Keycloak's database | Managed by Keycloak; sign-in and administration events 180 days |
| Logs: requests by method, path and status; counts and kinds; audit events with ids | The system journal | Capped at 1 GB; the oldest entries make way for new ones. No document text is ever logged |
| The model server's prompt cache: recent prompts, which include document passages | GPU memory and RAM of the model server | Until pushed out by newer prompts, or until the model server restarts |

The office chooses two of the periods above, at set-up or in the administrator's dashboard: how long closed cases are kept, and how long saved conversations are kept. Nothing is chosen for the office: until it chooses, cases and conversations are kept until someone deletes them.

## What deleting guarantees

There are three ways something leaves sūveryn: a person deletes it, it belongs to a case that is deleted, or a keep period passes. All three do the same thing underneath.

**At once.** The moment a delete succeeds, the item is removed from every path through which sūveryn reads it. A deleted document can no longer be listed, opened, searched, used to ground an answer, or cited; its passages, headings and file name are removed from every saved conversation that quoted them, for every member of the case, also in a conversation open in someone's browser at that moment. A deleted conversation can no longer be listed or opened by anyone, including a case member it was shared with. A deleted case takes its documents, their index, its conversations, its members and its access log with it, in that order, and if the documents cannot be deleted at that moment (the document service is not ready), the case stays and the hourly sweep tries again, so a case is never half deleted.

**Over time.** Underneath, these are ordinary database deletions. PostgreSQL does not overwrite a deleted row immediately: it marks it dead, and its housekeeping (autovacuum) reuses the space later, so the old bytes are overwritten by new data over time rather than at a fixed moment. Changes also pass through the database's write-ahead log, which is recycled continuously. So for a period that depends on how busy the office is, someone with full access to the appliance's disk and the right tools could recover traces of deleted text from the database's files. This is the gap the rest of this page is about.

**Off the machine, nothing.** The appliance's data partition is encrypted (LUKS2, unlocked by the machine's TPM or by the office's recovery key). A disk taken out of the machine, a decommissioned server, a disk sent for repair: none of them yield anything, deleted or not. This is the protection that matters for the realistic threat, and it covers everything the database housekeeping cannot, including the search index, the logs and the write-ahead log.

**In backups.** There are no backups yet (suveryn-tracker#33 builds them). When there are, a backup is a copy of the database as it was that day, encrypted for the office's offline recovery key; a document deleted after the backup was taken stays in that backup until the backup expires. The backup retention period is therefore the outer bound of this policy: "deleted" means "gone from the live system at once, and from every copy once the last backup that holds it has expired". A restore brings back only what was live at backup time.

## What is not covered, said plainly

- **The answers already given.** Deleting a document removes its passages from saved conversations, but an answer that restated a fact from the document keeps that sentence. The chat UI says so when a document is deleted and offers to delete those conversations too; the choice is the user's.
- **The prompt cache.** The model server keeps recent prompts, document passages included, in memory until they are pushed out or it restarts. A deleted document's passages can sit there for a while; they are not reachable through sūveryn, only by someone with access to the model server's memory on the running machine.
- **What left the box.** Passages copied to the clipboard, downloaded text, Word and Excel exports and printouts are outside sūveryn's control, and so is what the office does with them.
- **Someone with root on the running appliance** can read whatever is in memory at that moment, decrypted. No design changes that; it is why physical access to the appliance is the office's responsibility.
- **A development or test installation without the appliance** (a pod, a laptop) has no disk encryption unless its operator set it up; this policy's "off the machine" guarantee is the appliance's.

## Retention defaults

| Data | Default | Range | Where it is set |
|---|---|---|---|
| Closed cases | Until deleted by hand (`manual`) | 6 months, 1 year, 5 years, manual | Set-up (`--cases-keep`, `CASES_KEEP`), then the administrator's dashboard |
| Saved conversations | Until deleted by hand (`manual`) | 6 months, 1 year, 5 years, manual | Set-up (`--conversations-keep`, `CONVERSATIONS_KEEP`); the dashboard later |
| Case access log | 180 days | fixed | — |
| Keycloak sign-in and administration events | 180 days | fixed | The realm |
| System journal | 1 GB, oldest first | fixed | The image |
| Usage records | Indefinitely | — | A retention is added if an office needs one |
| Backups | Not built yet | To be decided in suveryn-tracker#33 | — |

A conversation's keep period counts from its last change, and applies to conversations in cases as well as in personal spaces: a conversation inside a case that is kept for five years can still expire after one, if the office chose one year for conversations. Cases keep the documents, conversations keep the questions and answers; the office sets each.

## Why no stronger claim

A design for cryptographic erasure exists (suveryn-tracker#31: a key per document and per conversation, wrapped under a master key in the TPM, rotated daily, so that destroying a key makes the leftover bytes meaningless within the rotation window). It was set aside, in proportion to where the product is: no customer has asked for it, the realistic threat (a disk out of the machine) is covered by disk encryption, GDPR accepts removal from the active system plus expiring backups, and a key hierarchy brings its own risk, a failed rotation or a TPM that will not unseal after a firmware update making all data unreadable, which is far likelier than a forensic recovery of dead rows. It will be picked up when there is a concrete need: a customer requirement, a certification, a regulator. Until then, nothing in sūveryn says "permanently", "securely" or "irrecoverably" deleted.

## Where this is enforced

- suveryn-core: [`docs/architecture.md`](https://github.com/suveryn/suveryn-core/blob/main/docs/architecture.md) §3 lists every place confidential data can exist, with its lifetime and protection, and §6 names the two gaps above as known limitations; the delete paths are `Store.delete_document`, `delete_scope`, `Conversations.delete`, `delete_case` and `purge`, and the gateway's `delete_case_everywhere` and hourly sweep.
- suveryn-appliance: the encrypted data partition ([`image/mkosi/README.md`](https://github.com/suveryn/suveryn-appliance/blob/main/image/mkosi/README.md)), the journal cap and no core dumps (`image/scripts/harden.sh`), the Keycloak event retention (`keycloak/realm/README.md`), and the two keep periods in `suveryn-provision`.
- The chat UI's wording for deleting a document, a conversation and a case, in the three languages, says what happens and never says "permanently".
