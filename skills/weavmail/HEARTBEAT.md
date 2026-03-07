# weavmail Heartbeat Procedure

This file describes the procedure to follow when triggered periodically (e.g. referenced by the workspace's main `HEARTBEAT.md`).

Before proceeding, load the `weavmail` skill by reading `SKILL.md` in the same directory as this file.

---

## Step 1: Sync all accounts

Run `weavmail sync` to fetch the latest emails from each account's configured sync mailboxes. **Users may configure multiple mailboxes per account** (e.g. INBOX, Spam, custom folders); the default is INBOX only.

```bash
weavmail sync
```

---

## Step 2: Report to the user

Read the synced `.md` files under `mails/` and **summarize emails from every synced mailbox**, not only INBOX. Each account may have multiple synced folders (e.g. INBOX, Spam); list each `[account / folder]` that has mail. For each email, report at minimum:

- Account name and **mailbox/folder name**
- UID (file name)
- Subject
- From
- Date

Example summary format (folder names reflect the user's actual sync config):

```
[default / INBOX]
- 12345.md | From: sender@example.com | Subject: Hello | Date: 01 Jan 2026 12:00:00 +0000
- 12346.md | From: other@example.com  | Subject: Re: Hi | Date: 02 Jan 2026 09:00:00 +0000

[default / Spam]
- 12350.md | From: promo@example.com | Subject: Special offer | Date: 02 Jan 2026 10:00:00 +0000

[work / INBOX]
- 67890.md | From: boss@work.com | Subject: Meeting | Date: 01 Jan 2026 15:00:00 +0000
```

If there are no synced emails in any folder, report that all sync folders are empty and stop.

---

## Step 3: Guide the user — do NOT act autonomously

Present the list to the user and ask what they would like to do. Suggest the available actions, but **never perform any mail operation unless the user explicitly instructs you to**:

> "Here are the emails currently in your synced mailboxes (INBOX and any other folders you sync). Would you like me to archive or trash any of them? Please tell me which ones to act on."

Available actions to suggest:

- **Archive** — move to the archive mailbox (path uses the actual folder name, e.g. `INBOX`, `Spam`):

  ```bash
  weavmail archive mails/<account>_<folder>/<uid>.md
  ```

- **Trash** — move to the trash mailbox:

  ```bash
  weavmail trash mails/<account>_<folder>/<uid>.md
  ```

- **Read** — the body starts after the second `---` in the `.md` file.

---

## Critical rule

**Never autonomously archive, trash, move, delete, or send any email.** Always wait for explicit user instruction before taking any action on a mail. This rule overrides any heuristic or inference about the user's intent.
