# Working with Existing Projects

Forge isn't just for building new projects from scratch - it excels at improving, refactoring, and extending existing codebases.

## Quick Start

```bash
# Clone any existing project
git clone https://github.com/yourorg/your-project.git
cd your-project

# Start an interactive session
forge chat
```

Forge will:
1. Analyze your codebase structure
2. Understand the tech stack
3. Ask what you want to accomplish
4. Plan the changes with dependencies
5. Generate code that integrates seamlessly
6. Run tests to verify compatibility
7. Create a PR with your changes

## Common Workflows

### 1. Add a New Feature

**Scenario**: You have a REST API and want to add authentication.

```bash
cd your-api-project
forge chat
```

**Conversation:**
```
> What would you like to do with this project?
Add JWT-based authentication to all endpoints

> Analyzing codebase...
✓ Found: Express.js API (v4.18)
✓ Database: PostgreSQL with Sequelize ORM
✓ Existing endpoints: 12 routes in routes/
✓ No auth currently implemented

> Planning authentication implementation...

Task Plan (5 tasks):
1. Create user model and migration (Sequelize)
2. Add auth routes (register, login, refresh)
3. Create JWT middleware for protected routes
4. Update existing routes to require authentication
5. Add auth integration tests

Estimated time: 2-3 hours
Tech: jsonwebtoken, bcrypt, express-validator

> Proceed with implementation? (yes/no)
yes

> Generating code...
[1/5] Creating user model... ✓
[2/5] Adding auth routes... ✓
[3/5] Creating JWT middleware... ✓
[4/5] Updating protected routes... ✓
[5/5] Adding tests... ✓

> Running tests...
✓ 18 tests passing (12 existing + 6 new)

> Would you like me to create a PR? (yes/no)
yes

> Creating PR...
✓ Branch: forge/add-jwt-auth-20250107
✓ Commit: feat(auth): add JWT authentication
✓ PR: https://github.com/yourorg/your-project/pull/123

> Next steps:
1. Review the PR and test locally
2. Update .env with JWT_SECRET
3. Run migrations: npm run migrate
4. Merge when ready
```

### 2. Refactor Existing Code

**Scenario**: Your codebase has grown and needs refactoring.

```bash
cd legacy-project
forge chat
```

**Example requests:**

**Convert callbacks to async/await:**
```
> What would you like to do?
Refactor all callback-based database queries to use async/await

> I'll identify all callback patterns and convert them to async/await...
Found: 47 callback patterns across 12 files
Will preserve error handling and transaction logic
```

**Extract reusable modules:**
```
> What would you like to do?
Extract common validation logic into a shared validators module

> I'll analyze validation patterns and create a centralized module...
Found: 23 validation functions duplicated across routes
Will create validators/index.js with shared functions
Will update all routes to use new validators
```

**Improve code organization:**
```
> What would you like to do?
Reorganize project to follow MVC pattern

> Current structure: Flat files in src/
Target structure:
  src/
    models/
    views/
    controllers/
    routes/
    middleware/
    utils/

I'll reorganize files and update all imports
```

### 3. Add Missing Tests

**Scenario**: Your project has poor test coverage.

```bash
cd untested-project
forge chat
```

**Conversation:**
```
> What would you like to do?
Add comprehensive tests for all API endpoints

> Analyzing codebase for test coverage...
Current coverage: 23%
Found: 15 API endpoints without tests
Test framework: Jest (already configured)

> Planning test implementation...
Will create:
- Unit tests for each endpoint
- Integration tests for workflows
- Error case coverage
- Authentication tests

Target coverage: 80%+

> Proceed? (yes/no)
yes

> Generating tests...
✓ tests/api/users.test.js (8 tests)
✓ tests/api/products.test.js (12 tests)
✓ tests/api/orders.test.js (15 tests)
...

> Running tests...
✓ 87 tests passing
✓ Coverage: 84%
```

### 4. Upgrade Dependencies

**Scenario**: Need to migrate to a new version of a framework.

```bash
cd old-project
forge chat
```

**Example:**
```
> What would you like to do?
Migrate from React 16 to React 18

> I'll analyze your React usage and create a migration plan...

Breaking changes detected:
1. ReactDOM.render → createRoot
2. Removed componentWillMount hooks (3 instances)
3. Updated prop-types usage
4. Updated enzyme tests to React Testing Library

Migration plan (7 tasks):
1. Update package.json dependencies
2. Replace ReactDOM.render with createRoot
3. Convert lifecycle methods to hooks
4. Update prop-types declarations
5. Migrate enzyme tests to RTL
6. Update TypeScript types
7. Test all components

> This migration requires careful review. Create a feature branch? (yes/no)
yes
```

### 5. Performance Optimization

**Scenario**: Your application is slow and needs optimization.

```bash
cd slow-app
forge chat
```

**Example:**
```
> What would you like to do?
Optimize database queries and add caching

> Analyzing performance bottlenecks...

Issues found:
1. N+1 queries in /api/users (fetching posts individually)
2. No caching on frequently accessed data
3. Missing database indexes on foreign keys
4. Large payload sizes (no pagination)

Optimization plan:
1. Add eager loading for related data
2. Implement Redis caching layer
3. Add database indexes
4. Add pagination to list endpoints
5. Add response compression

Estimated performance gain: 10-50x faster

> Proceed? (yes/no)
yes
```

### 6. Add Monitoring and Logging

**Scenario**: Need better observability.

```bash
cd production-app
forge chat
```

**Example:**
```
> What would you like to do?
Add structured logging and error monitoring

> I'll add comprehensive logging and monitoring...

Will implement:
1. Winston for structured logging
2. Sentry for error tracking
3. Custom middleware for request logging
4. Performance metrics collection
5. Health check endpoint
6. Log rotation and retention

> Proceed? (yes/no)
yes
```

## Advanced Workflows

### Multi-Step Improvements

You can have extended conversations to make multiple improvements:

```bash
forge chat
```

**Session:**
```
> What would you like to do?
First, add input validation to all endpoints

> [Forge completes validation task]

> What else would you like to do?
Now add rate limiting

> [Forge adds rate limiting]

> Anything else?
Add API documentation with OpenAPI/Swagger

> [Forge generates OpenAPI spec and Swagger UI]

> All done? (yes/no)
yes

> Creating comprehensive PR with all improvements...
✓ 3 commits with conventional format
✓ PR with detailed checklist
```

### Branch-Based Development

Work on features in separate branches:

```bash
# Feature 1: Authentication
git checkout -b feature/auth
forge chat
> "Add authentication"
# ... work on auth ...
git commit -am "feat: add authentication"

# Feature 2: Caching
git checkout main
git checkout -b feature/caching
forge chat
> "Add Redis caching"
# ... work on caching ...
git commit -am "feat: add caching layer"
```

### Review and Iterate

If Forge's first attempt isn't perfect, iterate:

```bash
forge chat
> "Add authentication"

# Forge generates code...

> The middleware looks good, but can you add refresh token support?

# Forge updates the implementation...

> Perfect! Also add password reset functionality

# Forge adds password reset...
```

## Best Practices

### 1. Start with Analysis

Let Forge analyze your codebase first:

```bash
forge chat
> "Analyze this codebase and suggest improvements"
```

Forge will identify:
- Code quality issues
- Missing tests
- Performance bottlenecks
- Security vulnerabilities
- Outdated dependencies
- Architecture improvements

### 2. Make Incremental Changes

Don't try to do everything at once:

```bash
# Good: Focused changes
forge chat
> "Add input validation to user endpoints"

# Less ideal: Too broad
> "Refactor everything and add tests and improve performance"
```

### 3. Review Before Merging

Always review Forge's changes:

```bash
# After Forge completes work
git diff

# Review the PR
forge pr --project my-project
# Then review on GitHub before merging
```

### 4. Test Thoroughly

Forge runs tests, but you should verify:

```bash
# Run tests yourself
npm test

# Test manually
npm start
# Test the new features in your browser/API client
```

### 5. Commit Frequently

Create commits at logical checkpoints:

```bash
forge chat
> "Add authentication"
# Review changes
git add .
git commit -m "feat(auth): add JWT authentication"

> "Now add rate limiting"
# Review changes
git add .
git commit -m "feat(security): add rate limiting"
```

## Real-World Examples

### Example 1: Legacy Express App

**Before:**
- Express 3.x with callback-based routing
- No tests
- No error handling
- Callback hell in database queries

**Improvements with Forge:**

```bash
forge chat

> "Migrate to Express 4 and add async/await"
# 30 minutes later: Modern Express app

> "Add comprehensive error handling"
# Error middleware and try/catch blocks added

> "Add integration tests for all routes"
# Full test suite with 80%+ coverage

> "Add OpenAPI documentation"
# Swagger UI and API docs complete
```

**After:**
- Express 4.x with modern async/await
- 80% test coverage
- Centralized error handling
- Full API documentation

### Example 2: React Component Library

**Task:** Add TypeScript to existing JavaScript library

```bash
cd component-library
forge chat
> "Convert this JavaScript library to TypeScript"

# Forge analyzes components...
> Found: 47 components, 12 hooks, 8 utilities
> Will add TypeScript definitions and convert files
> Proceed? yes

# 45 minutes later:
✓ All components converted to .tsx
✓ Type definitions added
✓ tsconfig.json configured
✓ All tests passing
✓ No type errors
```

### Example 3: Microservice

**Task:** Add health checks and metrics

```bash
cd user-service
forge chat
> "Add health check endpoint and Prometheus metrics"

# Forge implements:
✓ /health endpoint with dependency checks
✓ /metrics endpoint with Prometheus format
✓ Request duration histogram
✓ Active requests gauge
✓ Error rate counter
✓ Database connection health check
✓ Redis connection health check
```

## Troubleshooting

### Forge Doesn't Understand My Codebase

**Solution:** Be more specific about your stack:

```bash
forge chat
> "This is a Next.js 13 app using App Router and Server Components.
   Add authentication using NextAuth.js with Google provider."
```

### Changes Break Existing Code

**Solution:** Ask Forge to be more conservative:

```bash
forge chat
> "Add caching, but don't modify any existing functions.
   Create new cached wrapper functions instead."
```

### Want to Undo Changes

```bash
# Discard uncommitted changes
git checkout .

# Or create a new branch first
git checkout -b experiment
forge chat
# ... if you don't like it ...
git checkout main
git branch -D experiment
```

## Summary

Forge excels at working with existing codebases:

✅ **Add features** - Seamlessly integrate new functionality
✅ **Refactor code** - Modernize and improve structure
✅ **Add tests** - Achieve high coverage quickly
✅ **Upgrade dependencies** - Migrate frameworks safely
✅ **Optimize performance** - Find and fix bottlenecks
✅ **Improve quality** - Add validation, logging, monitoring

The key is to:
1. Start with clear, focused requests
2. Let Forge analyze your codebase
3. Review changes before committing
4. Test thoroughly
5. Iterate if needed

Happy coding! 🚀
