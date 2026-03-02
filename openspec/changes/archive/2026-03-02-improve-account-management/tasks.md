## 1. Config Storage Module

- [x] 1.1 Create `weavmail/config.py` module with account data structures
- [x] 1.2 Implement `get_config_path()` function to return `.weavmail/accounts.json` path
- [x] 1.3 Implement `load_accounts()` function to read and parse JSON config
- [x] 1.4 Implement `save_accounts()` function with atomic write (temp file + rename)
- [x] 1.5 Implement `ensure_config_dir()` function to create `.weavmail/` directory if missing
- [x] 1.6 Handle invalid JSON gracefully with clear error messages
- [x] 1.7 Return empty dict when config directory/file doesn't exist

## 2. Account Management Commands

- [x] 2.1 Implement `account config` with default name "default" when no argument provided
- [x] 2.2 Add interactive prompts for all 9 parameters (imap_host, imap_port, imap_username, imap_password, smtp_host, smtp_port, smtp_username, smtp_password, addresses)
- [x] 2.3 Show current values as defaults when updating existing account
- [x] 2.4 Parse addresses input (comma-separated) into array
- [x] 2.5 Allow partial configuration (empty values stored as null)
- [x] 2.6 Save account to config file after configuration

## 3. Account List Command

- [x] 3.1 Implement `account list` to display all account names
- [x] 3.2 Show "No accounts configured" message when empty
- [x] 3.3 Check each account for missing parameters
- [x] 3.4 Display warning for incomplete accounts (list missing fields)
- [x] 3.5 Exit with success code (0) even with warnings

## 4. Account Delete Command

- [x] 4.1 Implement `account delete <name>` to remove account from config
- [x] 4.2 Show "Account not found" error for non-existent accounts
- [x] 4.3 Exit with error code (1) when account doesn't exist
- [x] 4.4 Save updated config after deletion

## 5. Testing and Validation

- [x] 5.1 Test creating new account with all parameters
- [x] 5.2 Test updating existing account with partial values
- [x] 5.3 Test account list with complete and incomplete accounts
- [x] 5.4 Test account delete (existing and non-existing)
- [x] 5.5 Test default account name behavior
- [x] 5.6 Verify atomic file writes work correctly
- [x] 5.7 Test invalid JSON handling
