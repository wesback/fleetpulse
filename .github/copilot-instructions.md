# GitHub Copilot Custom Instructions

## Core Development Principles
- Write clean, readable, and maintainable code following established conventions for the current language
- Prioritize code clarity over cleverness - prefer explicit, self-documenting code
- Follow SOLID principles and appropriate design patterns
- Use meaningful variable and function names that clearly express intent
- Keep functions small and focused on a single responsibility

## Security Standards
- **Input Validation**: Always validate and sanitize all user inputs before processing
  - For Python/FastAPI: Use Pydantic models for request/response validation and type enforcement
  - For JavaScript/React: Sanitize and escape all user-generated content before rendering to prevent XSS
- **SQL Injection Prevention**: Use parameterized queries/prepared statements exclusively - never concatenate user input into SQL strings
- **Data Protection**: Never log sensitive data (passwords, tokens, PII) and use secure storage methods
- **Error Handling**: Implement secure error handling that doesn't expose system internals or stack traces to users
- **Dependency Security**: Use up-to-date, well-maintained libraries and regularly audit dependencies
- **Environment Variables**: Store sensitive configuration (API keys, database credentials, database URLs) in environment variables, never in code

## Code Quality & Maintainability
- **Documentation**: Include clear docstrings/comments for complex logic, API endpoints, and public interfaces
- **Error Handling**: Implement comprehensive error handling with appropriate logging and graceful degradation
- **Code Organization**: Use consistent file structure, logical module separation, and clear imports
- **Performance**: Consider performance implications and optimize where necessary without premature optimization
- **Refactoring**: Suggest refactoring opportunities when code becomes repetitive or overly complex

## Testing Requirements
- **Test Coverage**: Write unit tests for all business logic, edge cases, and error conditions
- **Test Structure**: Follow AAA pattern (Arrange, Act, Assert) for clear test organization
- **Mocking**: Use mocks/stubs for external dependencies to ensure isolated unit tests
- **Integration Tests**: Include integration tests for critical workflows and API endpoints
- **Test Data**: Use realistic but safe test data, avoid production data in tests
- **Test Naming**: Use descriptive test names that explain what is being tested and expected outcome
- **Test Organization**: Place all tests in a `/tests` directory at the project root
- **Testing Tools**: Use `pytest` for backend and `jest`/`react-testing-library` for frontend

## Language-Specific Guidelines
- **Python**: Follow PEP 8, use type hints, leverage context managers for resource handling
  - Leverage FastAPI’s dependency injection for authentication and authorization, use a virtual environment
- **JavaScript/TypeScript**: Use modern ES6+ features, prefer TypeScript for type safety, implement proper async/await handling
- **Java**: Follow Oracle conventions, use appropriate access modifiers, implement proper exception handling
- **C#**: Follow Microsoft conventions, use LINQ appropriately, implement proper disposal patterns
- **SQL**: Use proper indexing strategies, avoid SELECT *, use JOINs efficiently

## Database Best Practices
- Always use parameterized queries or ORM methods to prevent SQL injection
- Implement proper indexing for frequently queried columns
- Use transactions appropriately for data consistency
- Consider database performance impacts of queries and optimize when necessary
- Implement proper connection pooling and resource cleanup

## API Development
- **REST Standards**: Follow RESTful conventions for endpoint design and HTTP status codes
- **Input Validation**: Validate all request parameters and body content
- **Rate Limiting**: Implement appropriate rate limiting and throttling (consider middleware or proxies if needed)
- **Versioning**: Design APIs with versioning strategy from the start
- **Documentation**: Generate and maintain comprehensive API documentation (OpenAPI/Swagger, FastAPI auto-generated docs)

## Deployment & Operations
- **Configuration Management**: Use environment-specific configuration files
- **Logging**: Implement structured logging with appropriate log levels
- **Monitoring**: Include health checks and metrics collection points
- **Containerization**: Provide Docker configurations when appropriate
- **CI/CD**: Structure code to support automated testing and deployment pipelines

## Code Review Focus Areas
When suggesting improvements, prioritize:
1. Security vulnerabilities and potential attack vectors
2. Performance bottlenecks and scalability issues
3. Code maintainability and readability
4. Test coverage gaps and edge cases
5. Error handling completeness
6. Documentation clarity and completeness

## Response Format
- Provide complete, runnable code examples
- Include relevant imports and dependencies
- Add inline comments for complex logic
- Suggest alternative approaches when applicable
- Highlight potential security or performance considerations
- Include basic test examples for new functions