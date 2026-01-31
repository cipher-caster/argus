# Argus Documentation Index

**Last Updated**: 2026-01-31

Welcome to the Argus documentation! This guide helps you navigate the codebase efficiently.

---

## 🚀 Quick Start

**For AI Agents**: Start with [AI_AGENT_GUIDE.md](./AI_AGENT_GUIDE.md)

**For Developers**:

1. Read [AI_AGENT_GUIDE.md](./AI_AGENT_GUIDE.md) for overview
2. Review [Backend Architecture](./backend/ARCHITECTURE.md)
3. Review [Frontend Architecture](./frontend/ARCHITECTURE.md)
4. Check [Error Handling Guide](./backend/ERROR_HANDLING.md)

---

## � Documentation Structure

### Getting Started

- **[AI Agent Guide](./AI_AGENT_GUIDE.md)** - Comprehensive guide for AI agents and developers
  - Architecture overview
  - Key concepts (caching, error handling, validation)
  - Coding conventions
  - Common tasks
  - Recent improvements

### Backend

- **[Architecture](./backend/ARCHITECTURE.md)** - Backend system design (EXISTS - brief)
- **[Error Handling](./backend/ERROR_HANDLING.md)** - Custom exceptions and logging patterns
- **[Data Architecture](./backend/DATA_ARCHITECTURE.md)** - Data flow and storage (if exists)

### Frontend

- **[Architecture](./frontend/ARCHITECTURE.md)** - Frontend system design
  - Component patterns
  - State management
  - Performance optimizations
  - TypeScript patterns

### Other

- **[Analytics Service](./ANALYTICS_SERVICE.md)** - Analytics implementation
- **[Context](./CONTEXT.md)** - Project context and decisions
- **[Changelog](./CHANGELOG.md)** - Version history
- **[Roadmap](./ROADMAP.md)** - Future plans

---

## 🎯 Find What You Need

### "I want to understand the codebase"

→ [AI Agent Guide](./AI_AGENT_GUIDE.md)

### "I want to add a new API endpoint"

→ [AI Agent Guide - Common Tasks](./AI_AGENT_GUIDE.md#common-tasks)  
→ [Backend Architecture](./backend/ARCHITECTURE.md)  
→ [Error Handling](./backend/ERROR_HANDLING.md)

### "I want to add a new frontend component"

→ [Frontend Architecture - Component Patterns](./frontend/ARCHITECTURE.md#component-patterns)

### "I'm getting errors in my code"

→ [Error Handling Guide](./backend/ERROR_HANDLING.md)

### "I want to understand the data flow"

→ [AI Agent Guide - Architecture](./AI_AGENT_GUIDE.md#architecture-overview)  
→ [Backend Architecture - Data Flow](./backend/ARCHITECTURE.md)

### "I want to optimize performance"

→ [AI Agent Guide - Recent Improvements](./AI_AGENT_GUIDE.md#recent-improvements)  
→ [Frontend Architecture - Performance](./frontend/ARCHITECTURE.md#performance-optimizations)

---

## 📋 Documentation Maintenance

### When to Update Docs

**Update immediately**:

- New architecture patterns introduced
- Breaking changes to API
- New major features

**Update monthly**:

- Recent improvements section
- Common tasks section
- Troubleshooting section

**Update as needed**:

- Code examples (keep them current)
- Best practices (as they evolve)

### How to Update

1. **Identify affected docs** - Which files need updates?
2. **Make changes** - Update content, add examples
3. **Update "Last Updated" date** - At top of file
4. **Test code examples** - Verify they work
5. **Commit** - Clear commit message

---

## � Key Principles

These principles guide the Argus codebase:

1. **Type Safety** - Always use TypeScript/Python type hints
2. **Documentation** - Comprehensive docstrings and comments
3. **Error Handling** - Custom exceptions with clear messages
4. **Testing** - Write tests for all new features
5. **Performance** - Cache-aware, optimized queries
6. **Production Ready** - No debug logs, proper logging

---

## 🤝 Contributing

When contributing to Argus:

1. **Read relevant docs** before making changes
2. **Follow existing patterns** - Don't invent new ones
3. **Write tests** - For all new features
4. **Update docs** - If you change architecture/patterns
5. **Use conventions** - Logging, docstrings, validation

---

## 📝 Template for New Docs

When creating new documentation files:

```markdown
# Title

**Last Updated**: YYYY-MM-DD

Brief description of what this document covers.

---

## Section 1

Content...

## Section 2

Content...

---

## Related Documents

- [Link to related doc](./path/to/doc.md)
```

---

## 💡 Documentation Best Practices

1. **Be concise** - Get to the point quickly
2. **Use examples** - Show, don't just tell
3. **Keep updated** - Stale docs are worse than no docs
4. **Link liberally** - Connect related concepts
5. **Structure clearly** - Use headings, lists, code blocks

---

## 🔗 External Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **TanStack Query**: https://tanstack.com/query/latest
- **Pydantic**: https://docs.pydantic.dev/

---

**Questions?** Check the [AI Agent Guide](./AI_AGENT_GUIDE.md) first - it covers 90% of common scenarios!
