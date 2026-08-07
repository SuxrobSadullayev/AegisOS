# God Object Anti-Pattern

## Purpose

Documents the God Object anti-pattern, root causes, and refactoring strategies.

## Analysis

- **Symptom**: A single class or file contains thousands of lines of code handling unrelated concerns.
- **Root Cause**: Failure to enforce Single Responsibility Principle.
- **Refactoring Strategy**: Extract cohesive methods into dedicated domain service classes.
