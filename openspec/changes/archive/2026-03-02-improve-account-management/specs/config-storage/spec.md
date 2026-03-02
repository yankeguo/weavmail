## ADDED Requirements

### Requirement: Store configuration in JSON file
The system SHALL persist account configurations in a JSON file at `.weavmail/accounts.json`.

#### Scenario: Creating config directory on first use
- **WHEN** user runs `weavmail account config` for the first time
- **AND** `.weavmail/` directory does not exist
- **THEN** the system SHALL create the `.weavmail/` directory
- **AND** create the `.weavmail/accounts.json` file
- **AND** store the account configuration

#### Scenario: JSON file structure
- **WHEN** account configuration is saved
- **THEN** the JSON file SHALL contain an object with account names as keys
- **AND** each account value SHALL be an object with parameters as properties

### Requirement: Atomic configuration writes
The system SHALL write configuration files atomically to prevent corruption.

#### Scenario: Safe file write
- **WHEN** account configuration is updated
- **THEN** the system SHALL write to a temporary file first
- **AND** rename the temporary file to `.weavmail/accounts.json`
- **AND** ensure the configuration is never in a partially written state

### Requirement: Read configuration
The system SHALL read account configurations from `.weavmail/accounts.json`.

#### Scenario: Reading existing configuration
- **WHEN** user runs a command that requires account data
- **AND** `.weavmail/accounts.json` exists
- **THEN** the system SHALL read and parse the JSON file
- **AND** make account data available to commands

#### Scenario: Reading with no configuration
- **WHEN** user runs a command
- **AND** `.weavmail/` directory does not exist
- **THEN** the system SHALL treat it as empty configuration
- **AND** not raise an error

### Requirement: Handle invalid JSON
The system SHALL handle corrupted or invalid JSON gracefully.

#### Scenario: Invalid JSON file
- **WHEN** `.weavmail/accounts.json` contains invalid JSON
- **AND** user runs a command
- **THEN** the system SHALL display a clear error message indicating the file is corrupted
- **AND** exit with error code

### Requirement: Relative path storage
The system SHALL use `.weavmail/` directory relative to the current working directory.

#### Scenario: Config in current directory
- **WHEN** user runs `weavmail account list` from `/home/user/project/`
- **THEN** the system SHALL look for `.weavmail/accounts.json` at `/home/user/project/.weavmail/accounts.json`
- **AND** create it in that location if needed
