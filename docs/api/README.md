# API Documentation

This directory contains documentation related to the API of the AI Interviewer Agent.

## Contents

- [API Contracts](api_contracts.md): Documentation of the API contracts, including endpoints, request/response formats, and error handling.
- [Generated API Docs](api_docs/index.html): Auto-generated API documentation from code comments.

## API Documentation Guidelines

When documenting APIs:

1. Clearly document each endpoint's purpose, parameters, and return values
2. Include request/response examples
3. Document error codes and their meanings
4. Keep the documentation in sync with the actual implementation
5. Use standard formats (OpenAPI/Swagger) when possible

## Generating API Documentation

The API documentation can be generated automatically using the `docs_generator.py` script located in `backend/utils/`. This script will scan the codebase for API-related code and generate documentation in the `api_docs` directory.

To generate the API documentation:

```bash
python -m backend.utils.docs_generator
```

## Adding New API Documentation

When adding new API documentation:

1. Update the API contracts file with the new endpoint information
2. Update the API code with proper docstrings
3. Re-generate the API documentation
4. Verify the generated documentation is correct
