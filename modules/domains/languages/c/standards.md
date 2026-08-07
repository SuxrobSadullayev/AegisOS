# C Engineering Standards
<!-- Module ID: modules.domains.languages.c | Version: 1.0.0 | Token Budget: ~600 -->

## Purpose

Defines C memory management, pointer safety, undefined behavior prevention, and C11/C17 standards.

## Standards

- **Bounds Checking**: Use safe string/memory functions (`snprintf`, `memcpy_s`) instead of `strcpy` or `sprintf`.
- **Memory Allocation**: Every `malloc`/`calloc` MUST have a corresponding `free` and non-null check.
- **Compiler Warnings**: Code MUST compile with `-Wall -Wextra -Werror`.

## Anti-Patterns

- **Buffer Overflow**: Writing beyond array or string allocation limits.
- **Use After Free**: Accessing pointers after `free()`.

## Verification Checklist

- [ ] Are dynamic memory allocations checked for NULL?
- [ ] Are compiler warnings clean under `-Wall -Wextra -Werror`?
