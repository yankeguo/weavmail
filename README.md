# weavMail

A command-line email client designed for AI agents.

Available on [ClawHub](https://clawhub.ai/yankeguo/weavmail).

`weavmail` syncs emails from IMAP mailboxes to local Markdown files, and provides commands to list mailboxes, move messages, trash, archive, and send or reply to emails — all from the shell.

> **AI Agent Skill available** — install the weavmail skill for your AI agent with one command:
>
> ```bash
> npx skills add https://github.com/yankeguo/weavmail/tree/main/skills/weavmail -a openclaw -y
> ```

## Installation

```bash
pip install weavmail
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install weavmail
```

## Quick Start

```bash
# Configure an account (named "default")
weavmail account config \
  --imap-host imap.gmail.com \
  --smtp-host smtp.gmail.com \
  --username you@gmail.com \
  --password your-app-password \
  --addresses you@gmail.com

# List mailbox folders to identify Sent/Trash names
weavmail mailbox

# Optionally set Sent, Trash, Archive (names vary by provider)
weavmail account config --sent-mailbox "Sent" --trash-mailbox "Trash" --archive-mailbox "Archive"

# Optionally sync Spam in addition to INBOX
weavmail account config --sync-mailboxes "INBOX,Spam"

# Sync mail
weavmail sync

# Send a mail
weavmail send --to recipient@example.com --subject "Hello" --content body.txt
```

## Commands

### `account`

Manage mail account configurations stored in `.weavmail/accounts.json`.

```
weavmail account list
weavmail account config [NAME] [OPTIONS]
weavmail account delete NAME
```

| Option | Description |
|---|---|
| `--imap-host` | IMAP server hostname |
| `--imap-port` | IMAP port (default: 993, IMAPS/TLS) |
| `--imap-username` | IMAP login username |
| `--imap-password` | IMAP login password |
| `--smtp-host` | SMTP server hostname |
| `--smtp-port` | SMTP port (default: 465, SMTPS/TLS) |
| `--smtp-username` | SMTP login username |
| `--smtp-password` | SMTP login password |
| `--username` | Set both `imap-username` and `smtp-username` at once |
| `--password` | Set both `imap-password` and `smtp-password` at once |
| `--addresses` | Comma-separated list of sender addresses |
| `--sent-mailbox` | Mailbox to save sent mail (e.g. `Sent`, `[Gmail]/Sent Mail`) |
| `--trash-mailbox` | Trash mailbox (e.g. `Trash`, `[Gmail]/Trash`) |
| `--archive-mailbox` | Archive mailbox (e.g. `Archive`, `[Gmail]/All Mail`) |
| `--sync-mailboxes` | Comma-separated mailboxes to sync by default (e.g. `INBOX,Spam`); default is INBOX when unset |

`NAME` defaults to `"default"`. Only specified options are updated; omitted ones keep their existing values. Explicit `--imap-*` / `--smtp-*` options take precedence over `--username` / `--password`.

---

### `mailbox`

List all IMAP folders for an account. Use this to discover exact folder names (case-sensitive) before syncing non-INBOX mailboxes.

```
weavmail mailbox [--account NAME]
```

| Option | Default | Description |
|---|---|---|
| `--account` | `default` | Account to list folders for |

---

### `sync`

Fetch recent emails from IMAP mailbox(es) and save them as Markdown files under `./mails/<account>_<mailbox>/`. Uses all configured accounts and each account's `sync_mailboxes` config (default: INBOX).

```
weavmail sync [--limit N]
```

| Option | Default | Description |
|---|---|---|
| `--limit` | `10` | Max number of recent messages to fetch per mailbox |

Each email is saved as `<uid>.md` with a YAML front matter block:

```yaml
---
uid: "12345"
account: default
mailbox: INBOX
subject: Hello there
from: sender@example.com
to:
- you@gmail.com
cc: []
date: "01 Jan 2026 12:00:00 +0000"
flags: []
---

Mail body here...
```

Local files whose UID no longer exists on the server are automatically deleted.

---

### `move`

Move an email to another mailbox, then sync the source mailbox.

```
weavmail move MAIL_FILE DST_MAILBOX [--account NAME] [--sync-limit N]
```

`MAIL_FILE` is the path to a local `.md` file. Account and source mailbox are read from the file's front matter. Use `--account` to verify it matches the mail's account.

---

### `trash`

Move one or more emails to the account's trash mailbox, then sync the source mailbox.

```
weavmail trash MAIL_FILE [MAIL_FILE ...] [--sync-limit N]
```

Multiple `MAIL_FILE` arguments for batch operations. The trash mailbox is read from each mail's account `--trash-mailbox` config. Account is read from each file's front matter. Requires `trash_mailbox` to be configured for the account.

---

### `archive`

Move one or more emails to the account's archive mailbox, then sync the source mailbox.

```
weavmail archive MAIL_FILE [MAIL_FILE ...] [--sync-limit N]
```

Multiple `MAIL_FILE` arguments for batch operations. The archive mailbox is read from each mail's account `--archive-mailbox` config. Account is read from each file's front matter. Requires `archive_mailbox` to be configured for the account.

---

### `send`

Send a new email or reply to an existing one.

```
weavmail send [OPTIONS]
```

| Option | Description |
|---|---|
| `--account NAME` | Account to send from (default: `default`) |
| `--from ADDR` | Sender address (defaults to first configured address) |
| `--to ADDR` | Recipient address (repeatable) |
| `--cc ADDR` | CC address (repeatable) |
| `--bcc ADDR` | BCC address (repeatable) |
| `--subject TEXT` | Mail subject |
| `--content FILE` | File containing the mail body |
| `--reply MD_FILE` | Local `.md` file to reply to |
| `--no-save-sent` | Skip saving to Sent mailbox (for providers that auto-save, e.g. Gmail) |

**Reply mode** (`--reply`): subject, recipient, and sender address are inferred from the original mail's front matter. The original body is quoted and appended. `In-Reply-To` and `References` headers are set automatically.

```bash
# Send a new mail
weavmail send --to recipient@example.com --subject "Hello" --content body.txt

# Reply to a mail
weavmail send --reply mails/default_INBOX/12345.md --content reply.txt
```

## Mail File Format

Emails are stored at:

```
./mails/<account>_<mailbox>/<uid>.md
```

Special characters in account and mailbox names are replaced with `_` in the path. The original mailbox name (including `/`) is preserved in the front matter.

## Multiple Accounts

Configure additional accounts by providing a name:

```bash
weavmail account config work \
  --imap-host imap.work.com \
  --smtp-host smtp.work.com \
  --username you@work.com \
  --password your-password \
  --addresses you@work.com
```

Pass `--account` to target a specific account where supported:

```bash
weavmail mailbox --account work
weavmail send --account work --to someone@example.com --subject "Hi" --content body.txt
```

`weavmail sync` always syncs all configured accounts using each account's `sync_mailboxes` config. For `move` and `send --reply`, the account is read from the mail file's front matter; for `trash` and `archive`, the account is always read from each mail file.

## Notes

- Always sync before reading mail; read `.md` files directly (body starts after the second `---`).
- Mailbox names are case-sensitive — use `weavmail mailbox` to list exact names.
- All commands support `--help`, e.g. `weavmail sync --help`.

## License

MIT
