### Template Requirements (v0.4.0+)

Templates can declare their requirements using the `_requirements` field. This field is prefixed with underscore to indicate it's metadata, not a user-configurable variable.

#### Requirement Types

There are three database requirement types:

```json
{
  "_requirements": {
    "database": "none"       // No database - skip database prompts entirely
  }
}
```

```json
{
  "_requirements": {
    "database": "optional"   // Ask user if they want database
  }
}
```

```json
{
  "_requirements": {
    "database": "required"   // Force database selection
  }
}
```

#### Detailed Requirements with Messages

For better user experience, you can provide detailed requirements with custom messages:

```json
{
  "_requirements": {
    "database": {
      "type": "required",
      "message": "Auth template requires a database for user authentication"
    }
  }
}
```

#### Example: Base Template (No Database)

```json
{
  "_requirements": {
    "database": "none"
  },
  "project_name": "myapi",
  "description": "My API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": false,
  "database_type": "none"
}
```

**User Experience:**
- No database questions asked
- Project created without database setup
- Minimal template structure

#### Example: Auth Template (Required Database)

```json
{
  "_requirements": {
    "database": {
      "type": "required",
      "message": "Auth template requires a database for user authentication"
    }
  },
  "project_name": "my-auth-api",
  "description": "Authentication API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": true,
  "database_type": "postgresql"
}
```

**User Experience:**
- Message shown: "Auth template requires a database for user authentication"
- Prompt: "Which database would you like to use?"
- User must select a database type
- Project created with database setup

#### Example: Custom Template (Optional Database)

```json
{
  "_requirements": {
    "database": "optional"
  },
  "project_name": "mycustomapi",
  "description": "Custom API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": false,
  "database_type": "none"
}
```

**User Experience:**
- Prompt: "Would you like to set up a database?"
- If yes: "Which database would you like to use?"
- If no: Project created without database

**How Requirements Work:**
- `"none"` - Skip all database prompts, set `database_type = "none"`
- `"optional"` - Ask "Would you like to set up a database?" first
- `"required"` - Skip yes/no, ask "Which database?" directly
- Custom messages are shown before prompts for better context
- Requirements are validated before project creation to prevent broken templates

#### Benefits of Template-Level Control

1. **Template Author Control** - Template decides what features it needs
2. **No Hardcoded CLI Logic** - CLI interprets template requirements dynamically
3. **Extensible** - Easy to add new requirement types (python_version, redis, etc.)
4. **Better UX** - Users only see relevant questions for their chosen template
