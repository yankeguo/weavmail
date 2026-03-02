# weavmail

A command-line email client designed for AI agents.

Available on [ClawHub](https://clawhub.ai/yankeguo/weavmail).

`weavmail` syncs emails from IMAP mailboxes to local Markdown files, and provides commands to list mailboxes, move messages, and send or reply to emails — all from the shell.

> **AI Agent Skill available** — install the weavmail skill for your AI agent with one command:
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

# Sync the inbox
weavmail sync

# List mailbox folders
weavmail mailbox

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

`NAME` defaults to `"default"`. Only specified options are updated; omitted ones keep their existing values. Explicit `--imap-*` / `--smtp-*` options take precedence over `--username` / `--password`.

---

### `mailbox`

List all IMAP folders for an account.

```
weavmail mailbox [--account NAME]
```

---

### `sync`

Fetch recent emails from an IMAP mailbox and save them as Markdown files under `./mails/<account>_<mailbox>/`.

```
weavmail sync [--account NAME] [--mailbox FOLDER] [--limit N]
```

| Option | Default | Description |
|---|---|---|
| `--account` | `default` | Account name |
| `--mailbox` | `INBOX` | IMAP folder to sync |
| `--limit` | `10` | Max number of recent messages to fetch |

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
weavmail move MAIL_FILE DST_MAILBOX [--sync-limit N]
```

`MAIL_FILE` is the path to a local `.md` file. Account and source mailbox are read from the file's front matter.

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
| `--subject TEXT` | Mail subject |
| `--content FILE` | File containing the mail body |
| `--reply MD_FILE` | Local `.md` file to reply to |

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

## License

MIT
