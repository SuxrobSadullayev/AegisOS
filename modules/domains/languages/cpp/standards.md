# C++ Engineering Standards
<!-- Module ID: modules.domains.languages.cpp | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines C++17/C++20 standards, RAII, smart pointers, and Core Guidelines.

## Standards

- **RAII**: Resource acquisition MUST be tied to object lifetime (RAII).
- **Smart Pointers**: Prefer `std::unique_ptr` and `std::shared_ptr` over raw `new`/`delete`.
- **Const Correctness**: Member functions that do not modify state MUST be marked `const`.

## Anti-Patterns

- **Raw Ownership Pointers**: Managing dynamic memory with raw `T*` pointers.
- **C-Style Casts**: Using `(Type)val` instead of `static_cast` or `reinterpret_cast`.

## Verification Checklist

- [ ] Is RAII used for resource management?
- [ ] Are raw `new`/`delete` calls eliminated in favor of smart pointers?
