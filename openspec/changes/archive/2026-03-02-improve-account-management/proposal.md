## Why

The current weavmail CLI has stub implementations for account management. Users need a functional account configuration system that supports interactive setup and graceful handling of incomplete configurations. This change implements the account management capabilities needed for a production-ready email CLI tool.

## What Changes

- Implement `account config` command with interactive parameter configuration
- Support all email account parameters: IMAP/SMTP hosts, ports, usernames, passwords, and addresses
- Add default account name "default" for simplified single-account usage
- Modify `account list` to show warnings for incomplete configurations instead of forcing errors
- Implement configuration storage using a single JSON file
- Add `account delete` functionality for account removal

## Capabilities

### New Capabilities
- `account-management`: Interactive account configuration with support for creating, updating, listing, and deleting email accounts. Handles both complete and incomplete account setups gracefully.
- `config-storage`: Local configuration persistence using a single JSON file (`.weavmail/accounts.json`). The `.weavmail/` directory is auto-created if it doesn't exist.

### Modified Capabilities
- (none - no existing specs to modify)

## Impact

- CLI commands: `weavmail account list`, `weavmail account config`, `weavmail account delete`
- New dependencies: None (uses standard library + existing Click dependency)
- Config file: `.weavmail/accounts.json` (relative to current working directory)
- Config directory: `.weavmail/` (auto-created if it doesn't exist)
- Breaking changes: None - new functionality only
