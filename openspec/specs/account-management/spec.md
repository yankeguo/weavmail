# Capability: Account Management

## Purpose

Manage email account configurations for weavmail CLI.

## Requirements

### Requirement: Create or update account interactively
The system SHALL provide an interactive `account config` command that prompts for and stores account parameters.

#### Scenario: Creating a new account with all parameters
- **WHEN** user runs `weavmail account config default`
- **AND** system prompts for imap_host, imap_port, imap_username, imap_password, smtp_host, smtp_port, smtp_username, smtp_password, addresses
- **AND** user provides all values
- **THEN** the account SHALL be stored in `.weavmail/accounts.json`
- **AND** the command SHALL exit with success

#### Scenario: Updating an existing account
- **WHEN** user runs `weavmail account config existing_account`
- **AND** system prompts for each parameter showing current values as defaults
- **AND** user provides updated values
- **THEN** the existing account SHALL be updated with new values
- **AND** unchanged parameters SHALL retain their previous values

#### Scenario: Partial account configuration
- **WHEN** user runs `weavmail account config partial_account`
- **AND** user provides only imap_host and imap_username
- **THEN** the account SHALL be stored with provided values
- **AND** missing parameters SHALL be stored as null/empty

#### Scenario: Default account name
- **WHEN** user runs `weavmail account config` without a name argument
- **THEN** the system SHALL use "default" as the account name

### Requirement: List accounts with warnings
The system SHALL provide an `account list` command that displays all accounts and warns about incomplete configurations.

#### Scenario: Listing accounts with complete configuration
- **WHEN** user runs `weavmail account list`
- **AND** all accounts have complete configurations
- **THEN** system SHALL display all account names
- **AND** indicate they are complete
- **AND** exit with success code

#### Scenario: Listing accounts with incomplete configuration
- **WHEN** user runs `weavmail account list`
- **AND** some accounts have missing parameters
- **THEN** system SHALL display all account names
- **AND** list missing parameters for each incomplete account as warnings
- **AND** exit with success code (not error)

#### Scenario: Listing with no accounts configured
- **WHEN** user runs `weavmail account list`
- **AND** no accounts exist
- **THEN** system SHALL display "No accounts configured" message
- **AND** exit with success code

### Requirement: Delete accounts
The system SHALL provide an `account delete` command that removes accounts from configuration.

#### Scenario: Deleting an existing account
- **WHEN** user runs `weavmail account delete account_name`
- **AND** the account exists
- **THEN** the account SHALL be removed from `.weavmail/accounts.json`
- **AND** the command SHALL exit with success

#### Scenario: Deleting a non-existent account
- **WHEN** user runs `weavmail account delete nonexistent_account`
- **AND** the account does not exist
- **THEN** system SHALL display "Account not found" error
- **AND** exit with error code

### Requirement: Support all email account parameters
The system SHALL support the following account parameters: imap_host, imap_port, imap_username, imap_password, smtp_host, smtp_port, smtp_username, smtp_password, addresses.

#### Scenario: Storing all parameters
- **WHEN** user provides all nine parameters during account config
- **THEN** all values SHALL be stored in the account configuration

#### Scenario: Addresses as array
- **WHEN** user provides addresses parameter
- **AND** user inputs comma-separated email addresses
- **THEN** the system SHALL parse and store addresses as an array of strings
