## Context

weavmail is a CLI email client for AI agents with minimal stub implementations for account management. The `weavmail account` commands exist but do nothing. This design implements a complete account management system supporting interactive configuration, persistent storage, and graceful handling of incomplete setups.

**Current State:**
- CLI framework (Click) is already in place
- Account commands are defined as stubs: `account list`, `account config <name>`, `account delete <name>`
- No storage mechanism exists

**Constraints:**
- Follow KISS principle - simple, minimal implementation
- Single dependency limit: only use existing Click dependency
- No external config libraries (no PyYAML)
- Current working directory-based storage (not home directory)

## Goals / Non-Goals

**Goals:**
- Implement interactive `account config` command for creating/updating accounts
- Support all email parameters: IMAP/SMTP hosts, ports, usernames, passwords, addresses
- Store configuration in `.weavmail/accounts.json` (auto-create directory)
- Provide default account name "default" for single-account workflows
- Implement `account list` that warns about incomplete configs (no hard errors)
- Implement `account delete` for account removal
- Graceful handling of partial/missing configuration

**Non-Goals:**
- Account validation (testing IMAP/SMTP connectivity)
- Config file encryption or security hardening
- Multi-directory config support
- Account import/export
- GUI or web interface

## Decisions

### 1. JSON over YAML
**Decision:** Use JSON for configuration storage.
**Rationale:** 
- Standard library support (`json` module) - no additional dependencies
- Simpler implementation than YAML
- Human-readable enough for CLI tool

**Alternative considered:** YAML - rejected to avoid adding PyYAML dependency

### 2. Single File vs Directory of Files
**Decision:** Store all accounts in single `.weavmail/accounts.json` file.
**Rationale:**
- Simpler file management
- Atomic read/write operations
- Easier to backup/inspect entire configuration
- Suitable for small account sets (AI agent use case)

**Alternative considered:** One file per account - rejected as unnecessary complexity

### 3. Interactive vs Flag-Based Configuration
**Decision:** Interactive configuration in `account config` command.
**Rationale:**
- Better UX for AI agents - can prompt for missing values
- Allows partial configuration (set some values now, others later)
- Cleaner CLI without many optional flags
- Matches user request for "逐次配置每个参数"

**Alternative considered:** `--imap-host`, `--smtp-host` flags - rejected in favor of interactive flow

### 4. Warning vs Error for Incomplete Configs
**Decision:** `account list` shows warnings for incomplete accounts, doesn't error.
**Rationale:**
- Allows gradual account setup
- User can see which fields are missing
- Non-blocking workflow - can use partially configured accounts for read-only operations

### 5. File Structure
```
.weavmail/
└── accounts.json
```

**Account JSON schema:**
```json
{
  "default": {
    "imap_host": "imap.example.com",
    "imap_port": 993,
    "imap_username": "user@example.com",
    "imap_password": "secret",
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_username": "user@example.com",
    "smtp_password": "secret",
    "addresses": ["user@example.com", "alias@example.com"]
  }
}
```

### 6. Module Organization
**Decision:** Add account management logic to existing `cli.py` or create `config.py` module.
**Rationale:**
- Start with `config.py` module for separation of concerns
- Keep `cli.py` focused on command definitions
- Config module handles file I/O and account operations

## Risks / Trade-offs

**[Risk] Plain text password storage** → **Mitigation:** Document security limitations; users can use app-specific passwords

**[Risk] No configuration validation** → **Mitigation:** List command shows missing fields; validation deferred to connection time

**[Risk] Single JSON file corruption** → **Mitigation:** Use atomic write (write to temp, then rename); minimal acceptable for MVP

**[Risk] Concurrent access conflicts** → **Mitigation:** Document as single-user tool; no file locking for simplicity

## Migration Plan

**Deployment:**
1. Create `.weavmail/` directory on first account config
2. Write `accounts.json` with new account
3. No migration needed (no existing data to migrate)

**Rollback:**
- Simply delete `.weavmail/` directory to remove all configuration
- Or delete individual accounts with `account delete <name>`

## Open Questions

- Should we support config file environment variable override? (e.g., `WEAVMAIL_CONFIG_DIR`)
- Should passwords be base64 encoded to avoid escaping issues in JSON?
- Should we add a `weavmail account show <name>` command to view single account details?
