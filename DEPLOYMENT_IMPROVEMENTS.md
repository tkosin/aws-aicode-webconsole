# Deployment Improvements for Multi-Project Development

Based on the developer journey scenarios (multiple projects + local dev servers), here are recommended improvements to the deployment.

---

## ✅ Current Status

### What's Already Working

1. **Container Isolation** ✓
   - Each developer has isolated Docker container
   - 1.5 CPU cores, 4GB RAM per developer
   - Separate workspace directories

2. **Basic Tools** ✓
   - Docker and Docker Compose installed on EC2
   - AWS CLI v2
   - CloudWatch agent

3. **Persistent Storage** ✓
   - 500GB EBS volume
   - Workspace persists across restarts
   - Daily backups

---

## 🔧 Recommended Improvements

### 1. Development Tools Installation

**Current Issue**: code-server containers lack common dev tools

**Solution**: Add tools to containers via startup script or custom image

#### Option A: Add to User Data (EC2 level - affects all containers)

Add to `cdk/stacks/compute_stack.py` user data:

```python
# After Docker installation, before container start
"# Install additional development tools",
"apt-get install -y tmux htop lsof net-tools",
"",
```

#### Option B: Create Custom code-server Image (Recommended)

Create `cdk/scripts/Dockerfile.code-server`:

```dockerfile
FROM codercom/code-server:latest

# Install development tools
USER root
RUN apt-get update && apt-get install -y \
    tmux \
    htop \
    lsof \
    net-tools \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18 (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install PM2 globally
RUN npm install -g pm2

# Install common Python packages
RUN pip3 install --no-cache-dir \
    virtualenv \
    pipenv

# Switch back to coder user
USER coder

# Set default shell to bash
ENV SHELL=/bin/bash
```

Update `docker-compose.yml`:

```yaml
services:
  code-server-dev1:
    build:
      context: .
      dockerfile: Dockerfile.code-server
    # Or use pre-built image:
    # image: your-registry/code-server-dev:latest
    ...
```

### 2. Docker-in-Docker Support

**For developers who need to run Docker containers inside code-server**

Update `docker-compose.yml`:

```yaml
services:
  code-server-dev1:
    ...
    privileged: true  # Required for Docker-in-Docker
    volumes:
      - /mnt/ebs-data/dev1/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev1/config:/home/coder/.local/share/code-server
      - /var/run/docker.sock:/var/run/docker.sock  # Share Docker socket
```

**Pros**: Developers can run `docker run`, `docker-compose`
**Cons**: Security concern (privileged mode), containers share host Docker

**Alternative (More Secure)**: Use Podman or limit Docker access

### 3. Shared PostgreSQL Container

**For teams sharing databases across multiple projects**

Add to `docker-compose.yml`:

```yaml
services:
  # ... existing code-server services ...

  shared-postgres:
    image: postgres:15
    container_name: shared-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - /mnt/ebs-data/shared/postgres:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  shared-redis:
    image: redis:7-alpine
    container_name: shared-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - /mnt/ebs-data/shared/redis:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

Update compute_stack.py to create shared directories:

```python
"# Create shared services directory",
"mkdir -p /mnt/ebs-data/shared/{postgres,redis}",
"chown -R ubuntu:ubuntu /mnt/ebs-data/shared",
```

### 4. Port Mapping Documentation

**Create port allocation guide for developers**

Add to `docker-compose.yml` comments:

```yaml
# Port Allocation Guide:
#
# Code-server UI:          8443-8450 (dev1-dev8)
# Frontend apps:           3000-3099 (use inside containers)
# Node.js backends:        4000-4099 (use inside containers)
# Python backends:         8000-8099 (use inside containers)
# Shared PostgreSQL:       5432
# Shared Redis:            6379
# Mock/Test services:      5000-5099
#
# Note: Ports 3000-8099 are accessed via VS Code port forwarding
#       Only code-server UI ports (8443-8450) are exposed via ALB
```

### 5. Resource Monitoring Dashboard

**Add container monitoring script**

Create `/home/ubuntu/monitor-resources.sh`:

```bash
#!/bin/bash
# Monitor all developer container resources

echo "======================================"
echo "Developer Container Resource Usage"
echo "Date: $(date)"
echo "======================================"
echo ""

# Docker stats (CPU, Memory per container)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "======================================"
echo "Disk Usage"
echo "======================================"
df -h /mnt/ebs-data | tail -1

echo ""
echo "======================================"
echo "Port Usage"
echo "======================================"
netstat -tulpn | grep LISTEN | grep -E ":(3000|4000|5432|6379|8000)" || echo "No dev servers running"

echo ""
echo "======================================"
echo "Top Processes by Memory"
echo "======================================"
ps aux --sort=-%mem | head -10
```

Add to user data:

```python
"# Create monitoring script",
"cat > /home/ubuntu/monitor-resources.sh << 'EOFSCRIPT'",
"<script content here>",
"EOFSCRIPT",
"chmod +x /home/ubuntu/monitor-resources.sh",
"chown ubuntu:ubuntu /home/ubuntu/monitor-resources.sh",
```

### 6. Startup Helper Scripts

**Create helper scripts for common tasks**

Create `/home/ubuntu/dev-tools/`:

```bash
# start-project.sh
#!/bin/bash
PROJECT=$1
cd ~/workspace/$PROJECT
tmux attach -t $PROJECT || tmux new -s $PROJECT

# stop-all-servers.sh
#!/bin/bash
echo "Stopping all Node.js servers..."
pkill -f "node.*dev"
echo "Stopping all Python servers..."
pkill -f "python.*uvicorn"
echo "Stopping all npm processes..."
pkill -f "npm.*run"
echo "Done!"

# check-ports.sh
#!/bin/bash
echo "=== Open Ports ==="
netstat -tulpn | grep LISTEN | grep -E ":(3000|3001|3002|4000|4001|8000|8001|5432|6379)"
```

### 7. Pre-installed Development Dependencies

**For faster project setup**

Add to Dockerfile.code-server or user data:

```dockerfile
# Common Node.js global packages
RUN npm install -g \
    typescript \
    ts-node \
    nodemon \
    npm-check-updates \
    serve \
    json-server

# Common Python packages
RUN pip3 install --no-cache-dir \
    black \
    flake8 \
    pytest \
    ipython \
    requests \
    fastapi \
    uvicorn
```

### 8. Git Configuration Template

**Pre-configure git for developers**

Add to user data or container startup:

```bash
# Create global .gitconfig template
cat > /home/coder/.gitconfig << EOF
[user]
    # Developers should update these
    name = Developer Name
    email = dev@example.com

[core]
    editor = code --wait
    autocrlf = input

[pull]
    rebase = false

[init]
    defaultBranch = main

[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD
EOF
```

### 9. VS Code Settings Sync

**Create workspace settings for optimal multi-project dev**

Create `/home/coder/.local/share/code-server/User/settings.json`:

```json
{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "editor.formatOnSave": true,
  "terminal.integrated.defaultProfile.linux": "bash",
  "workbench.startupEditor": "none",
  "explorer.confirmDelete": false,
  "git.autofetch": true,
  "git.confirmSync": false,
  "extensions.ignoreRecommendations": false,

  // Claude Code settings (if needed)
  "claude.apiEndpoint": "https://bedrock-runtime.ap-southeast-1.amazonaws.com",
  "claude.authType": "aws",
  "claude.awsRegion": "ap-southeast-1"
}
```

---

## 📋 Implementation Priority

### High Priority (Implement Now)

1. **Development Tools** (Option B: Custom Docker image)
   - Critical for multi-project workflow
   - Implementation: 1-2 hours

2. **Port Allocation Guide** (Documentation)
   - Prevents port conflicts
   - Implementation: 15 minutes

3. **Resource Monitoring Script**
   - Helps developers manage resources
   - Implementation: 30 minutes

### Medium Priority (Nice to Have)

4. **Shared Database Containers**
   - Useful for teams
   - Implementation: 1 hour

5. **Helper Scripts**
   - Improves developer experience
   - Implementation: 1 hour

6. **Pre-installed Dependencies**
   - Faster project setup
   - Implementation: 30 minutes

### Low Priority (Optional)

7. **Docker-in-Docker**
   - Only if developers need it
   - Security consideration required

8. **Git Configuration**
   - Developers can set up themselves
   - Nice automation

9. **VS Code Settings**
   - Personal preference varies
   - Provide as template

---

## 🚀 Quick Implementation Plan

### Phase 1: Essential Tools (Week 1)

```bash
# 1. Create custom code-server Dockerfile
cd cdk/scripts/
# Create Dockerfile.code-server (see above)

# 2. Build and push image (optional - or build on EC2)
docker build -t code-server-dev:v1 -f Dockerfile.code-server .
docker tag code-server-dev:v1 your-registry/code-server-dev:v1
docker push your-registry/code-server-dev:v1

# 3. Update docker-compose.yml
# Change image from codercom/code-server:latest
# to: your-registry/code-server-dev:v1

# 4. Create monitoring script
# Add to user data in compute_stack.py

# 5. Re-deploy
cdk deploy code-server-multi-dev-compute
```

### Phase 2: Shared Services (Week 2)

```bash
# 1. Add postgres and redis to docker-compose.yml
# 2. Update compute_stack.py user data (create shared dirs)
# 3. Re-deploy
# 4. Test database access from containers
```

### Phase 3: Helper Scripts (Week 3)

```bash
# 1. Create dev-tools directory structure
# 2. Add helper scripts
# 3. Update documentation
# 4. Train developers on usage
```

---

## ⚠️ Considerations

### Resource Constraints

Current setup: t3.2xlarge (8 vCPU, 32GB RAM)

With improvements:
```
8 developers × 4GB     = 32GB (full capacity)
Shared PostgreSQL      = 512MB
Shared Redis           = 256MB
System overhead        = ~2GB

Total: ~34.8GB required
```

**Recommendation**:
- Keep current setup but monitor closely
- Consider upgrading to t3.4xlarge (16 vCPU, 64GB RAM) if resource issues occur
- Or reduce per-developer RAM to 3.5GB (allows more headroom)

### Security

**Docker Socket Sharing**:
- If enabling Docker-in-Docker, review security implications
- Container can potentially affect other containers
- Consider using rootless Docker or Podman

**Shared Databases**:
- Each project should use separate database (CREATE DATABASE project_a)
- Don't share credentials across all projects
- Consider using AWS RDS for production-like setup

### Cost Impact

**Additional costs**:
- Custom Docker image: $0 (build on EC2)
- Shared containers: Minimal (already within instance)
- Monitoring: $0 (using existing tools)

**Potential savings**:
- Pre-installed tools → Faster onboarding → Less idle time
- Shared databases → Less resource usage per developer

---

## 📊 Before vs After

### Before (Current)
```
- Basic code-server container
- No dev tools pre-installed
- Each developer installs own tools
- No shared services
- Manual resource monitoring
```

### After (With Improvements)
```
✓ Development tools pre-installed (tmux, htop, etc.)
✓ Node.js and Python ready to use
✓ Shared PostgreSQL and Redis
✓ PM2 for process management
✓ Resource monitoring script
✓ Helper scripts for common tasks
✓ Port allocation guide
✓ Git configured
```

### Developer Experience Impact

**Setup Time**:
- Before: 30-60 minutes per project (install tools, dependencies)
- After: 5-10 minutes per project (dependencies only)

**Resource Management**:
- Before: Manual monitoring, guess when to stop services
- After: One command shows all resource usage

**Database Setup**:
- Before: Install PostgreSQL per project or use SQLite
- After: Shared PostgreSQL ready, just CREATE DATABASE

---

## 🎯 Conclusion

**Must Have** (Implement ASAP):
1. Custom Docker image with dev tools
2. Port allocation documentation
3. Resource monitoring script

**Should Have** (Within 2 weeks):
4. Shared database containers
5. Helper scripts

**Nice to Have** (Future):
6. Docker-in-Docker (if needed)
7. Git templates
8. VS Code settings

**Next Steps**:
1. Review this document with team
2. Prioritize based on team needs
3. Implement Phase 1 (essential tools)
4. Gather developer feedback
5. Iterate and improve

---

**Last Updated**: 2026-01-19
**Status**: Proposed Improvements
**Implementation Owner**: DevOps Team
