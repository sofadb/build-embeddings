# Learning Notes: Docker Optimization

## Key Takeaways
- Use multi-stage builds to reduce image size
- Leverage build cache effectively with proper layer ordering
- .dockerignore is crucial for faster builds

## Best Practices
1. Put least-changing layers first (dependencies)
2. Most-changing layers last (source code)
3. Use specific base image tags, not `latest`

Reference: https://docs.docker.com/develop/dev-best-practices/
