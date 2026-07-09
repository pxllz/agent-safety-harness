# Security Policy

## Scope

`agent-safety-harness` is a small library for experimenting with autonomous
agents in **sandboxed environments only**. By design it contains:

- no network calls,
- no integrations with real brokers, exchanges, or external execution systems,
- no credential handling of any kind.

The only execution backend is `FakeBroker`, which records actions in memory
and never touches the outside world. If you wire this library to a real
execution system, you are outside the supported scope of this project and
responsible for your own risk controls.

## Reporting a Vulnerability

If you find a security issue (for example, a way to bypass a gate, defeat
idempotency, or forge an approval), please report it privately via
[GitHub private vulnerability reporting](https://github.com/pxllz/agent-safety-harness/security/advisories/new)
rather than opening a public issue.

Please include:

- a short description of the issue and its impact,
- a minimal reproduction if possible.

You can expect an acknowledgement within a reasonable time frame. This is a
small volunteer-maintained project, so please be patient.

## Supported Versions

Only the latest release on the `main` branch is supported.
