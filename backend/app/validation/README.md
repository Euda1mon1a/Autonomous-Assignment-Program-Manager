# Request Validation Package

Comprehensive request validation decorators for FastAPI routes.

## Features

- **@validate_request**: Comprehensive validation for query params and request body
- **@validate_query**: Query parameter validation
- **@validate_body**: Request body validation
- **Custom validation rules**: Reusable validation logic
- **Cross-field validation**: Validate relationships between multiple fields
- **Conditional validation**: Apply rules based on other field values
- **Localized error messages**: Support for multiple languages (EN, ES, FR)
- **Validation context**: Track and accumulate errors during validation

## Quick Start

### Basic Query Validation

```python
from app.validation import validate_query, required, numeric_range

@router.get("/people")
@validate_query({
    "page": [required, numeric_range(min_value=1)],
    "limit": [numeric_range(min_value=1, max_value=100)]
})
async def list_people(page: int, limit: int = 20):
    return {"page": page, "limit": limit}
```

### Basic Body Validation

```python
from app.validation import validate_body, required, string_length, email_format

@router.post("/users")
@validate_body({
    "name": [required, string_length(min_length=1, max_length=100)],
    "email": [required, email_format()]
})
async def create_user(request: Request):
    body = await request.json()
    return body
```

### Cross-Field Validation

```python
from app.validation import validate_request, ValidationContext

def validate_dates(data: dict, ctx: ValidationContext):
    if data.get("start_date") > data.get("end_date"):
        ctx.add_field_error("end_date", "Must be after start date")

@router.post("/schedules")
@validate_request(
    body_rules={
        "start_date": [required],
        "end_date": [required]
    },
    cross_field_validator=validate_dates
)
async def create_schedule(request: Request):
    body = await request.json()
    return body
```

### Conditional Validation

```python
from app.validation import (
    validate_body,
    validate_conditional_field,
    required,
    pgy_level_rule,
    person_type_rule
)

@router.post("/people")
@validate_body({
    "name": [required],
    "type": [required, person_type_rule()]
})
@validate_conditional_field(
    field="pgy_level",
    condition_field="type",
    condition_value="resident",
    rules=[required, pgy_level_rule()]
)
async def create_person(request: Request):
    # pgy_level is only required when type="resident"
    body = await request.json()
    return body
```

## Available Validation Rules

### Basic Rules

- `required`: Field must be present and not None/empty
- `string_length(min_length, max_length)`: String length validation
- `numeric_range(min_value, max_value)`: Numeric range validation
- `enum_values(allowed_values)`: Enum/choice validation
- `regex_pattern(pattern, error_message)`: Regex pattern matching

### Format Rules

- `email_format()`: Email address validation
- `uuid_format()`: UUID format validation
- `date_range(min_date, max_date)`: Date range validation
- `phone_number_rule()`: US phone number format

### Domain-Specific Rules

- `pgy_level_rule()`: PGY level (1-3) validation
- `person_type_rule()`: Person type (resident/faculty)
- `faculty_role_rule()`: Faculty role validation
- `positive_number_rule()`: Positive number validation
- `percentage_rule()`: Percentage (0-100) validation

### Collection Rules

- `list_items(item_rule, min_items, max_items)`: List validation
- `all_of(*rules)`: All rules must pass
- `any_of(*rules)`: At least one rule must pass

### Advanced Rules

- `conditional(condition, rule)`: Apply rule based on condition
- `custom(validator, error_message)`: Custom validation function

## Convenience Decorators

### Pagination

```python
from app.validation import validate_pagination

@router.get("/items")
@validate_pagination(max_limit=100)
async def list_items(page: int = 1, limit: int = 20):
    return {"page": page, "limit": limit}
```

### Date Range

```python
from app.validation import validate_date_range_params

@router.get("/reports")
@validate_date_range_params()
async def get_report(start_date: date, end_date: date):
    # Validates start_date <= end_date
    return {"start": start_date, "end": end_date}
```

### UUID Parameter

```python
from app.validation import validate_uuid_param

@router.get("/people/{person_id}")
@validate_uuid_param("person_id")
async def get_person(person_id: str):
    return {"id": person_id}
```

## Error Response Format

When validation fails, the API returns a 422 Unprocessable Entity response:

```json
{
  "detail": {
    "message": "Validation failed",
    "errors": [
      {
        "type": "required",
        "field": "name",
        "message": "Name is required",
        "params": {}
      },
      {
        "type": "invalid_format",
        "field": "email",
        "message": "Email has invalid format",
        "params": {}
      }
    ]
  }
}
```

## Localization

The package supports multiple languages for error messages:

```python
from app.validation import validate_body, required, Locale

@router.post("/users")
@validate_body(
    rules={"name": [required]},
    locale=Locale.ES_ES  # Spanish error messages
)
async def create_user(request: Request):
    body = await request.json()
    return body
```

Supported locales:
- `Locale.EN_US` - English (default)
- `Locale.ES_ES` - Spanish
- `Locale.FR_FR` - French

## Validation Context

The validation context tracks errors and allows storing data for cross-field validation:

```python
from app.validation import validation_scope

with validation_scope() as ctx:
    ctx.add_field_error("field1", "Custom error")
    ctx.set_data("user_id", "123")

    if ctx.has_errors():
        errors = ctx.get_errors_list()
```

## Best Practices

1. **Use Pydantic schemas for complex validation**: The decorators are best for simple, reusable validation rules. For complex models, use Pydantic schemas.

2. **Combine with existing validators**: The package complements the existing `app.validators` module. Use both together.

3. **Keep rules reusable**: Create custom rules for domain-specific validation that can be reused across routes.

4. **Use cross-field validation for dependencies**: When one field depends on another, use cross-field validation instead of complex individual rules.

5. **Leverage conditional validation**: For fields that are required based on other fields, use conditional validation decorators.

6. **Test your validation**: Write tests for custom validation rules and complex validation logic.

## Examples

See `examples.py` in this package for comprehensive examples of all validation features.

## Architecture

The validation package is organized as follows:

- **decorators.py**: Validation decorators for routes
- **rules.py**: Reusable validation rule functions
- **context.py**: Validation context for error tracking
- **messages.py**: Localized error messages
- **examples.py**: Usage examples

## Integration with Existing Code

This package integrates seamlessly with the existing codebase:

- Works alongside Pydantic schemas
- Complements `app.validators` module
- Uses FastAPI's dependency injection
- Returns standard HTTP 422 responses
- Follows project's async/await patterns

## Testing

Run tests with:

```bash
cd backend
pytest tests/test_validation_decorators.py -v
```

## Future Enhancements

Potential improvements:

- [ ] Async validation rules for database checks
- [ ] Custom locale message files
- [ ] Validation rule composition DSL
- [ ] Integration with OpenAPI schema generation
- [ ] Performance optimizations for large payloads
