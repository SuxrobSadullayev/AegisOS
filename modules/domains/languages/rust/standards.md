# Rust Engineering Standards
<!-- Module ID: modules.domains.languages.rust | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines Rust memory safety, error handling, borrowing, and idiomatic practices.

## Standards

- **Error Handling**: Use `Result` and `Option` types with explicit `?` propagation instead of `panic!`.
- **Borrow Checker**: Prefer immutable references (`&T`) over mutable ones (`&mut T`).
- **Clippy**: Code MUST compile cleanly without `cargo clippy` warnings.

## Anti-Patterns

- **Excessive `.unwrap()`**: Calling `.unwrap()` in production paths.
- **Unsafe Blocks Without Justification**: `unsafe` code without safety comments.

## Verification Checklist

- [ ] Are `.unwrap()` calls avoided in favor of `?` error propagation?
- [ ] Does `cargo clippy` pass with zero warnings?
