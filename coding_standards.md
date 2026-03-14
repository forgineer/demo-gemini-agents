# Migration Coding Standards - Java

## 1. Core Principles
- **Explicit Typing:** Always define types for function parameters and return values. Do not use generic `Object` if a more specific class exists.
- **Null Safety:** Where applicable, prefer standard null-checks or use `Optional<T>` for return types that might be empty.
- **Code Only:** When generating output, return only the code block. Do not include conversational filler like "Here is your code" or "Sure!"

## 2. Naming Conventions
- **Classes:** Use PascalCase (e.g., `AccountValidator`).
- **Methods/Variables:** Use camelCase (e.g., `calculateTotalAmount`).
- **Constants:** Use SCREAMING_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`).

## 3. Specific Library Preferences
- **Date Handling:** Use `java.time` (LocalDate, LocalDateTime) exclusively. Do not use legacy `java.util.Date`.
- **Collections:** Prefer `List<T>` and `Map<K, V>` interfaces over concrete implementations like `ArrayList` or `HashMap` in signatures.
- **Custom Classes:** If you see logic involving a calculation, always check if it can be mapped to our internal `com.company.finance.MathUtils` library.

## 4. Error Handling
- **Try/Catch:** Wrap database or network calls in try-catch blocks.
- **Logging:** Use `LoggerFactory` for logging errors. Do not use `System.out.println`.
- **Custom Exceptions:** If a business rule is violated, throw a `ValidationException` rather than returning a null or a generic error string.

## 5. Prohibited Patterns (The "Never" List)
- Never use "Magic Numbers"—define them as constants.
- Do not use hardcoded configuration values; assume they will be injected via a `ConfigService`.
- Avoid deeply nested `if-else` blocks; prefer guard clauses (early returns).

## 6. Example Pattern: Guard Clause
Instead of:
```java
if (result != null) {
    if (result.isValid()) {
        // do work
    }
}
```

Use:
```java
if (result == null || !result.isValid()) {
    return;
}
// do work
```