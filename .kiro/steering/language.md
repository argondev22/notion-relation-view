# Code and Commit Message Language

## Language Standards

All code, comments, commit messages, and technical documentation must be written in **English**.

## Scope

### Must Be in English

- Source code (variables, functions, classes, methods)
- Code comments and docstrings
- Commit messages
- Pull request descriptions
- Issue descriptions
- API documentation
- Technical specifications
- README files
- Configuration files with comments

### Can Be in Other Languages

- User-facing content (UI text, error messages shown to end users)
- Product documentation for specific markets
- Internal team communication (Slack, meetings, etc.)

## Rationale

- **Global Collaboration**: English enables international team members to contribute
- **Industry Standard**: Most programming languages, frameworks, and tools use English
- **Code Readability**: Consistent language improves code comprehension
- **Tooling Compatibility**: Many development tools expect English identifiers
- **Knowledge Sharing**: English documentation is accessible to the broader developer community

## Examples

✅ **Correct**:

```python
def calculate_user_subscription_fee(user_id: str) -> float:
    """Calculate the monthly subscription fee for a user."""
    # Fetch user's subscription tier
    tier = get_subscription_tier(user_id)
    return tier.monthly_price
```

```text
feat(subscription): add monthly fee calculation

Implement function to calculate user subscription fees based on tier.
```

❌ **Incorrect**:

```python
def ユーザー料金計算(user_id: str) -> float:
    """ユーザーの月額料金を計算する"""
    # ユーザーのサブスクリプションティアを取得
    tier = get_subscription_tier(user_id)
    return tier.monthly_price
```

```text
feat(subscription): 月額料金計算機能を追加

ティアに基づいてユーザーのサブスクリプション料金を計算する機能を実装。
```

## AI Assistant Behavior

When generating code or commit messages, the AI assistant must:

- Always use English for code identifiers
- Always use English for comments and docstrings
- Always use English for commit messages
- Always use English for technical documentation
- Translate any Japanese requirements or discussions into English when writing code
