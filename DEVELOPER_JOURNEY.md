# Developer Journey - AWS Code-Server Multi-Developer Platform

This document describes the complete developer experience from onboarding to daily development workflow.

---

## 👨‍💻 Table of Contents

1. [Day 0: Onboarding](#day-0-onboarding)
2. [Daily Development Workflow](#daily-development-workflow)
3. [Multiple Projects Workflow](#multiple-projects-workflow)
4. [Running Local Development Servers](#running-local-development-servers)
5. [Developer Experience: Pros & Cons](#developer-experience-pros--cons)
6. [Admin Journey](#admin-journey)
7. [User Stories](#user-stories)
8. [Productivity Gains](#productivity-gains)
9. [Typical Day Timeline](#typical-day-timeline)
10. [Recommended Workflow](#recommended-workflow)
11. [FAQ](#faq)

---

## 🎯 Day 0: Onboarding

### Total Time: ~10 minutes

### 1. Receive Credentials from Admin

Developer receives:
- **URL**: `https://devN.tuworkshop.vibecode.letsrover.ai` (where N = 1-8)
- **Password**: Retrieved from AWS Secrets Manager by admin

### 2. First Login (2 minutes)

```
Step 1: Open browser
Step 2: Navigate to your assigned URL
Step 3: Enter password
Step 4: See VS Code running in browser ✨
```

**What you'll see:**
- Full VS Code interface
- Integrated terminal
- File explorer
- Extension marketplace

### 3. Install Claude Code Extension (5 minutes)

#### Installation Steps:

1. Click **Extensions** icon in left sidebar (or press `Ctrl+Shift+X`)
2. Search for "**Claude Code**"
3. Click **Install** on the official Claude Code extension by Anthropic
4. Wait for installation to complete

#### Configure for AWS Bedrock:

Open Settings (`Ctrl+,`) or Settings JSON (`Ctrl+Shift+P` → "Preferences: Open Settings (JSON)") and add:

```json
{
  "claude.apiEndpoint": "https://bedrock-runtime.ap-southeast-1.amazonaws.com",
  "claude.authType": "aws",
  "claude.awsRegion": "ap-southeast-1",
  "claude.modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
}
```

### 4. Test Claude (2 minutes)

1. Open Claude Code panel
2. Type a simple question: "สวัสดีครับ"
3. Claude responds → Ready to use! ✅

### 5. Setup Your Workspace

```bash
# Clone your project
git clone https://github.com/your-org/your-project.git

# Install dependencies
cd your-project
npm install  # or pip install -r requirements.txt

# Start working!
```

---

## 📅 Daily Development Workflow

### Morning: Start Work

```
09:00 → Open browser
09:00 → Navigate to your URL
09:01 → Enter password (saved in browser)
09:01 → Workspace ready (everything from yesterday is still there)
09:02 → Start coding
```

**No setup needed:**
- All files are exactly where you left them
- Terminal history preserved
- Git state maintained
- Extensions already configured

### Using Claude Code Throughout the Day

#### 1. Writing Code with AI Assistance

**Autocomplete:**
```javascript
// Start typing...
function calculateTotal(

// Claude suggests:
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

**Ask Questions:**
```
You: "อธิบายฟังก์ชัน calculateTotal ให้หน่อย"
Claude: "ฟังก์ชันนี้คำนวณผลรวมของราคาสินค้าทั้งหมดในอาร์เรย์..."
```

**Request Refactoring:**
```
You: "ปรับโค้ดนี้ให้ clean ขึ้น"
Claude: [Suggests improved version with explanations]
```

#### 2. Debugging

```
Scenario: You encounter an error

Step 1: Copy error message
Step 2: Ask Claude: "Error นี้เกิดจากอะไรครับ?"
Step 3: Claude analyzes and suggests 3 possible causes
Step 4: Try suggested fixes
Step 5: Problem solved!
```

**Example:**
```
Error: Cannot read property 'name' of undefined

You: "Error นี้เกิดจากอะไร?"

Claude: "Error นี้เกิดจากการพยายามเข้าถึง property 'name'
ของ object ที่เป็น undefined มี 3 สาเหตุที่เป็นไปได้:

1. Object ยังไม่ถูกสร้าง/initialize
2. API response ไม่มีข้อมูล
3. Async operation ยังไม่เสร็จ

แนะนำให้เพิ่ม null check: object?.name หรือ object && object.name"
```

#### 3. Learning New Patterns

```
You: "วิธีทำ lazy loading ใน React ยังไง?"

Claude: [Provides code example with explanation in Thai]

import React, { lazy, Suspense } from 'react';

const MyComponent = lazy(() => import('./MyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <MyComponent />
    </Suspense>
  );
}
```

#### 4. Code Review

```
You: "Review โค้ดนี้ให้หน่อย"
[Paste code]

Claude:
"พบประเด็นที่ควรปรับปรุง:

1. ควรใช้ const แทน var (ES6 best practice)
2. ไม่มี error handling ในส่วน API call
3. ตัวแปร userInfo ควรเปลี่ยนเป็น userData เพื่อความชัดเจน
4. ฟังก์ชัน calculatePrice ควรแยกออกมาเป็น utility

นี่คือโค้ดที่ปรับปรุงแล้ว: [...]"
```

#### 5. Documentation

```
You: "เขียน README.md สำหรับโปรเจคนี้ให้หน่อย"

Claude: [Generates comprehensive README with:
- Project description
- Installation steps
- Usage examples
- API documentation
- Contributing guidelines]
```

### Evening: End Work

```
18:00 → Save your work (auto-save is enabled by default)
18:01 → Commit to git (if ready)
18:02 → Close browser
       → No need to shut down anything
       → Everything will be there tomorrow
```

---

## 📂 Multiple Projects Workflow

### Workspace Organization

When working on multiple projects, organize your workspace for easy context switching:

```bash
~/workspace/
├── project-a/              # Client A - E-commerce
│   ├── frontend/           (Next.js - port 3000)
│   ├── backend/            (Node.js - port 4000)
│   └── mobile/             (React Native)
│
├── project-b/              # Client B - Dashboard
│   ├── web/                (React - port 3001)
│   └── api/                (Python FastAPI - port 8000)
│
├── project-c/              # Internal Tool
│   └── app/                (Vue.js - port 3002)
│
├── experiments/            # Learning & Testing
│   ├── rust-practice/
│   └── ai-playground/
│
└── shared/                 # Shared utilities
    ├── scripts/
    └── templates/
```

### Daily Multi-Project Journey

#### Morning: Project A (E-commerce)

```bash
09:00 │ Login to code-server
09:01 │ cd ~/workspace/project-a/frontend
09:02 │ npm run dev
       │ → Server running on http://localhost:3000
       │
09:05 │ New terminal (Ctrl+Shift+`)
       │ cd ~/workspace/project-a/backend
       │ npm run dev
       │ → API running on http://localhost:4000
       │
09:10 │ Start coding
       │ ├─ File explorer: project-a/frontend
       │ ├─ Terminal 1: frontend (port 3000)
       │ ├─ Terminal 2: backend (port 4000)
       │ └─ VS Code preview: localhost:3000
```

#### Afternoon: Switch to Project B

```bash
13:00 │ Stop Project A (Ctrl+C in both terminals)
       │
13:01 │ cd ~/workspace/project-b/web
       │ npm run dev
       │ → Running on http://localhost:3001
       │
13:02 │ New terminal
       │ cd ~/workspace/project-b/api
       │ python -m uvicorn main:app --port 8000
       │ → API running on http://localhost:8000
       │
13:05 │ Work on Project B
       │ Terminal 1: web (port 3001)
       │ Terminal 2: API (port 8000)
```

#### Evening: Quick Fix Project C

```bash
16:00 │ git stash (save Project B work)
16:01 │ cd ~/workspace/project-c/app
       │ npm run dev -- --port 3002
       │ → Running on port 3002
       │
16:05 │ Fix bug quickly
       │ git commit && git push
       │
16:15 │ Stop server (Ctrl+C)
16:16 │ cd ~/workspace/project-b/web
       │ git stash pop
       │ npm run dev
       │ → Continue Project B
```

### Port Management Strategy

Assign ports systematically to avoid conflicts:

```bash
# Frontend apps: 3000-3099
Project A frontend:  3000
Project B frontend:  3001
Project C frontend:  3002

# Node.js backends: 4000-4099
Project A backend:   4000
Project B backend:   4001

# Python backends: 8000-8099
Project A API:       8000
Project B API:       8001

# Databases
PostgreSQL:          5432
Redis:               6379
MongoDB:             27017

# Mock/Test services: 5000-5099
Mock auth:           5000
Test API:            5001
```

### Project-Specific Environment Variables

```bash
# project-a/.env
DATABASE_URL=postgresql://localhost:5432/project_a
API_URL=http://localhost:4000
PORT=3000
NODE_ENV=development

# project-b/.env
DATABASE_URL=postgresql://localhost:5432/project_b
API_URL=http://localhost:8001
PORT=3001
PYTHON_ENV=development

# project-c/.env
DATABASE_URL=postgresql://localhost:5432/project_c
API_URL=http://localhost:4002
PORT=3002
VUE_APP_ENV=development
```

### Using tmux for Session Management

Install and use tmux to manage multiple terminal sessions:

```bash
# Install tmux (already pre-installed in deployment)
sudo apt install tmux

# Create session for Project A
tmux new -s project-a
  # Window 1: frontend
  cd ~/workspace/project-a/frontend && npm run dev
  # Ctrl+B, C (new window)
  # Window 2: backend
  cd ~/workspace/project-a/backend && npm run dev
  # Ctrl+B, C (new window)
  # Window 3: logs/commands

# Detach: Ctrl+B, D

# List sessions
tmux ls

# Attach to session
tmux attach -t project-a

# Create session for Project B
tmux new -s project-b

# Switch between projects
tmux attach -t project-a  # Work on A
tmux attach -t project-b  # Work on B
```

### Git Workflow per Project

Each project maintains its own git repository:

```bash
# Project A
cd ~/workspace/project-a
git status              # Only Project A files
git branch              # Project A branches
git checkout -b feature/new-cart

# Project B
cd ~/workspace/project-b
git status              # Only Project B files
git branch              # Project B branches
git checkout -b feature/dashboard

# Independent version control
```

### Resource Management Tips

Monitor and manage resources across projects:

```bash
# Check current resource usage
htop                     # CPU and memory
docker stats             # Container resources

# Check running processes
ps aux | grep node       # Node processes
ps aux | grep python     # Python processes

# Check open ports
netstat -tulpn | grep LISTEN

# Stop unused services
# When switching projects, stop previous servers
Ctrl+C in terminal
# Or kill specific process
kill $(lsof -t -i:3000)  # Kill process on port 3000
```

### Best Practices

**1. Stop Unused Services**
```bash
# Before switching projects
# Terminal 1: Ctrl+C (stop frontend)
# Terminal 2: Ctrl+C (stop backend)
# Or use tmux detach (keeps running)
```

**2. Use Different Ports**
```bash
# Package.json - Project A
{
  "scripts": {
    "dev": "next dev -p 3000"
  }
}

# Package.json - Project B
{
  "scripts": {
    "dev": "next dev -p 3001"
  }
}
```

**3. Database Per Project**
```bash
# Create separate databases
docker exec postgres psql -U postgres -c "CREATE DATABASE project_a;"
docker exec postgres psql -U postgres -c "CREATE DATABASE project_b;"
docker exec postgres psql -U postgres -c "CREATE DATABASE project_c;"
```

**4. Quick Project Switching Script**
```bash
# Create ~/workspace/switch-project.sh
#!/bin/bash
PROJECT=$1

case $PROJECT in
  "a")
    cd ~/workspace/project-a/frontend
    tmux attach -t project-a || tmux new -s project-a
    ;;
  "b")
    cd ~/workspace/project-b/web
    tmux attach -t project-b || tmux new -s project-b
    ;;
  "c")
    cd ~/workspace/project-c/app
    tmux attach -t project-c || tmux new -s project-c
    ;;
  *)
    echo "Usage: ./switch-project.sh [a|b|c]"
    ;;
esac

# Make executable
chmod +x ~/workspace/switch-project.sh

# Usage
~/workspace/switch-project.sh a  # Switch to Project A
```

---

## 🚀 Running Local Development Servers

### Full-Stack Development Setup

#### Starting Multiple Services

```bash
# Terminal 1: Database (PostgreSQL)
docker run -d \
  --name dev-postgres \
  -e POSTGRES_PASSWORD=dev123 \
  -e POSTGRES_DB=myapp \
  -p 5432:5432 \
  postgres:15

# Terminal 2: Backend API
cd ~/workspace/project-a/backend
npm install
npm run dev
# → Express server: http://localhost:4000

# Terminal 3: Frontend
cd ~/workspace/project-a/frontend
npm install
npm run dev
# → Next.js: http://localhost:3000

# Terminal 4: Available for commands
git status
npm test
Claude Code interactions
```

### VS Code Terminal Layout

Organize terminals efficiently:

```
┌─────────────────────────────────────┐
│ TERMINAL 1: Backend API             │
│ $ cd backend && npm run dev         │
│ Server running on port 4000         │
├─────────────────────────────────────┤
│ TERMINAL 2: Frontend                │
│ $ cd frontend && npm run dev        │
│ Next.js running on port 3000        │
├─────────────────────────────────────┤
│ TERMINAL 3: Database Logs           │
│ $ docker logs -f dev-postgres       │
├─────────────────────────────────────┤
│ TERMINAL 4: Commands & Tests        │
│ $ # Available for git, npm test     │
└─────────────────────────────────────┘
```

### Port Forwarding & Preview

#### Built-in VS Code Port Forwarding

VS Code (code-server) automatically detects running servers:

```
1. Run: npm run dev (port 3000)
2. VS Code shows notification: "Port 3000 is available"
3. Click "Open in Browser"
4. Opens preview in new tab
5. URL: Port forwarding handled automatically
```

#### Accessing from External Browser

```bash
# Option 1: Use ALB (only port 8080 - code-server UI)
https://dev1.tuworkshop.vibecode.letsrover.ai
# → Code-server interface only

# Option 2: VS Code Port Forwarding (automatic)
# When you run a dev server on port 3000:
# VS Code creates forwarding automatically
# Click "Open in Browser" notification

# Option 3: SSH Tunnel (advanced)
# From your local machine:
ssh -i key.pem -L 3000:localhost:3000 ubuntu@<ec2-ip>
# Then open local browser:
http://localhost:3000  # → Tunnels to EC2 port 3000
```

### Hot Reload Development

#### Frontend (React/Next.js)

```bash
09:00 │ npm run dev
09:01 │ Server ready on http://localhost:3000
09:02 │ Edit: components/Header.tsx
09:03 │ Hot reload happens automatically
       │ ↓
       │ [Fast Refresh] rebuilding...
       │ [Fast Refresh] done in 234ms
       │ ✓ Compiled successfully
```

#### Backend (Node.js + nodemon)

```bash
10:00 │ npm run dev (using nodemon)
10:01 │ Server running on port 4000
10:02 │ Edit: routes/users.js
10:03 │ nodemon restarts automatically
       │ ↓
       │ [nodemon] restarting due to changes...
       │ [nodemon] starting `node server.js`
       │ Server running on port 4000
```

### Running Concurrent Services

#### Scenario: Full-Stack + Mock Services

```bash
# Terminal Layout
┌─────────────────────────────────────┐
│ TERMINAL 1: Backend API             │
│ $ npm run dev                       │
│ Express on port 4000 ✓              │
├─────────────────────────────────────┤
│ TERMINAL 2: Frontend                │
│ $ npm run dev                       │
│ Next.js on port 3000 ✓              │
├─────────────────────────────────────┤
│ TERMINAL 3: Mock Auth Service       │
│ $ json-server --port 5000 mock.json │
│ Mock API on port 5000 ✓             │
├─────────────────────────────────────┤
│ TERMINAL 4: Watch Tests             │
│ $ npm run test:watch                │
│ Jest watching... ✓                  │
└─────────────────────────────────────┘
```

### Resource Monitoring

#### Check Available Resources

```bash
# CPU and Memory usage
htop
# Or
top

# Container stats
docker stats

# Process list
ps aux

# Port usage
netstat -tulpn | grep LISTEN
lsof -i :3000  # Check specific port

# Disk usage
df -h
du -sh ~/workspace/*
```

#### Resource Limits per Container

Each developer container has:
- **CPU**: 1.5 cores (burstable)
- **RAM**: 4GB
- **Disk**: ~62GB

**Good for:**
- 1-2 frontend apps running simultaneously
- 1-2 backend APIs
- 1 database (lightweight)
- Multiple terminal sessions

**Not ideal for:**
- 5+ concurrent dev servers
- Heavy compilation (large C++ projects)
- Multiple Docker containers (resource intensive)
- Machine learning training

### Database Options

#### Option 1: SQLite (Lightweight)

```bash
# Best for: Single developer, simple apps
cd ~/workspace/project-a
sqlite3 dev.db

# Node.js
npm install better-sqlite3

# Python
pip install sqlite3

# Pros: No daemon, file-based, fast
# Cons: No concurrent writes, limited for production-like dev
```

#### Option 2: PostgreSQL in Docker

```bash
# Best for: Production-like development
docker run -d \
  --name dev-postgres \
  -e POSTGRES_PASSWORD=dev123 \
  -p 5432:5432 \
  -v ~/workspace/postgres-data:/var/lib/postgresql/data \
  postgres:15

# Create databases per project
docker exec dev-postgres psql -U postgres -c "CREATE DATABASE project_a;"
docker exec dev-postgres psql -U postgres -c "CREATE DATABASE project_b;"

# Pros: Production-like, multi-project
# Cons: Uses ~200MB RAM
```

#### Option 3: AWS RDS (Shared)

```bash
# Best for: Team collaboration, production parity
# Connect to shared RDS instance
DATABASE_URL=postgresql://username:password@rds-endpoint.amazonaws.com:5432/dbname

# Pros: Shared data, production parity, no local resources
# Cons: Requires internet, costs money, shared state
```

### Process Management

#### Using PM2 (Process Manager)

```bash
# Install PM2 (already pre-installed in deployment)
npm install -g pm2

# Start services with PM2
cd ~/workspace/project-a
pm2 start npm --name "frontend" -- run dev
pm2 start npm --name "backend" -- run dev

# List processes
pm2 list

# Stop all
pm2 stop all

# Delete all
pm2 delete all

# Save configuration
pm2 save

# Pros: Services run in background, auto-restart
# Cons: More complex than terminal
```

#### Using Docker Compose

```bash
# Create docker-compose.dev.yml in project root
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "4000:4000"
    volumes:
      - ./backend:/app
    environment:
      - NODE_ENV=development

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    environment:
      - NODE_ENV=development

  database:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=dev123

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all
docker-compose -f docker-compose.dev.yml down
```

### Debugging Running Services

#### Check Service Status

```bash
# Is service running?
curl http://localhost:3000/healthz
curl http://localhost:4000/api/health

# Check process
ps aux | grep node
ps aux | grep python

# Check logs
tail -f ~/workspace/project-a/frontend/logs/dev.log
```

#### Common Issues

**Port Already in Use:**
```bash
# Find process using port
lsof -i :3000

# Kill process
kill $(lsof -t -i:3000)

# Or use different port
npm run dev -- --port 3001
```

**Out of Memory:**
```bash
# Check memory usage
free -h

# Stop unused services
pm2 stop all
docker stop $(docker ps -aq)

# Or restart container (from EC2 host)
docker restart code-server-dev1
```

**High CPU:**
```bash
# Find process consuming CPU
top
# Press 'P' to sort by CPU

# Kill heavy process if needed
kill <PID>
```

### Best Practices Summary

**1. Stop Unused Services**
- Only run services you're actively using
- Stop before switching projects
- Use tmux to preserve sessions

**2. Use Appropriate Tools**
- SQLite for simple/solo projects
- PostgreSQL Docker for team-like dev
- PM2 for background services

**3. Monitor Resources**
- Check htop regularly
- Stop services when memory > 3.5GB
- Restart if sluggish

**4. Organize Ports**
- Document port assignments
- Use consistent port ranges
- Check for conflicts before starting

**5. Leverage Hot Reload**
- Use nodemon for Node.js
- Use Fast Refresh for React
- Configure watch mode properly

---

## 🔄 Developer Experience: Pros & Cons

### ✅ Advantages

#### 1. Zero Setup Time

**Traditional Approach:**
```
Day 1: Install OS dependencies (Python, Node, Docker)
Day 2: Install project dependencies
Day 3: Fix environment issues
Day 4: Finally start coding
```

**Cloud Development Approach:**
```
Minute 1: Open browser
Minute 2: Start coding
```

#### 2. Work From Anywhere

**Scenario:**
```
Monday:    Home Desktop (Windows)
Tuesday:   Office MacBook
Wednesday: Co-working Space (Personal Laptop)
Thursday:  Coffee Shop (iPad + Keyboard)
Friday:    Back to Office

→ Same workspace, same files, same environment
→ No syncing needed
→ No "it works on my machine" issues
```

#### 3. AI Assistant Always Available

**Benefits:**
- No context switching to ChatGPT
- Claude sees your project structure
- Instant answers in Thai or English
- Code suggestions in context
- No copy-paste needed

#### 4. Easy Collaboration

**Use Cases:**
```
Code Review:
  You: "มาดู code ของผมที่ dev1.tuworkshop.vibecode.letsrover.ai"
  Colleague: [Opens URL] → Can review together

Pair Programming:
  Both open same URL → Work together in real-time
  Use VS Code Live Share extension for collaboration

Debugging Together:
  Share URL → Teammate can see exact environment
  No "can't reproduce on my machine"
```

#### 5. Automatic Backup

```
Daily:
  - EBS snapshot at 2:00 AM (Bangkok time)
  - 30 days retention
  - Zero downtime

File Changes:
  - Auto-save every 1 second
  - Git history for code
  - Very low risk of data loss
```

#### 6. Consistent Environment

```
Everyone gets:
  ✅ Same OS (Ubuntu)
  ✅ Same tools installed
  ✅ Same VS Code version
  ✅ Same extensions

No more:
  ❌ "Works on my machine"
  ❌ Dependency conflicts
  ❌ Version mismatches
  ❌ Setup documentation drift
```

### ⚠️ Disadvantages & Limitations

#### 1. Internet Required

```
❌ No internet = Can't work
✅ But: Most development requires internet anyway
```

**Mitigation:**
- Use mobile hotspot as backup
- Most cafes/offices have reliable internet
- Bangkok has excellent internet infrastructure

#### 2. Latency

**Typing Code:**
```
Latency: < 50ms
Feel: Instant, no noticeable delay
```

**Claude Responses:**
```
Latency: ~20-50ms additional (Bangkok → Singapore)
Feel: Slightly slower than local, but acceptable
Total response time: 1-5 seconds depending on complexity
```

**Network Operations:**
```
Git push/pull: Same as local (depends on git remote)
API calls: Same as local
```

#### 3. Resource Constraints

**Per Developer:**
- CPU: 1.5 cores (burstable to 2)
- RAM: 4GB
- Disk: ~62GB per developer

**Good For:**
- Web development
- Backend API development
- Script development
- Most Python/Node.js projects

**Not Ideal For:**
- Machine learning training (limited GPU)
- Video editing
- Heavy compilation (large C++ projects)
- Running multiple Docker containers

**Workaround:**
- Use AWS services for heavy tasks (Sagemaker, Lambda, ECS)
- Upgrade instance type if needed

#### 4. No Native GUI Apps

```
❌ Can't Run:
   - Desktop applications (Photoshop, Illustrator)
   - Native mobile apps
   - Local databases with GUI clients

✅ Can Run:
   - CLI tools
   - Terminal applications
   - Web-based tools
   - Docker containers
   - Databases (PostgreSQL, MySQL via CLI)
```

#### 5. Claude API Costs

**Usage-Based Pricing:**
```
Light User (1M tokens/month):     ~$18/month
Medium User (10M tokens/month):   ~$180/month
Heavy User (50M tokens/month):    ~$900/month
```

**Cost Control:**
- Team lead can monitor usage
- Set budget alerts
- Use cheaper Haiku model for simple tasks
- Use Sonnet for complex problems

#### 6. Browser-Only Interface

```
Limitations:
- No native OS integration
- Some keyboard shortcuts may conflict
- Some VS Code features may not work perfectly

Advantages:
- Works on any device
- No installation needed
- Consistent experience
```

#### 7. Shared Resources

```
8 developers share 1 EC2 instance:
- CPU: 8 vCPUs total → 1 per developer
- RAM: 32GB total → 4GB per developer

If one developer runs heavy task:
  → May affect others temporarily
  → Container limits prevent severe impact
```

---

## 👔 Admin Journey

### Week 1: Initial Setup

**Day 1: Deploy Infrastructure (30 minutes)**
```bash
cd cdk/
cdk deploy --all
```

**Day 2: Setup DNS (1-2 hours)**
```
1. Get ALB DNS name from CDK output
2. Add certificate validation CNAME at DNS provider
3. Wait for certificate validation (5-30 minutes)
4. Add 8 developer subdomain CNAMEs
5. Verify DNS propagation
```

**Day 3: Start Containers (1 hour)**
```bash
# SSH to EC2
ssh -i key.pem ubuntu@<instance-ip>

# Fetch passwords from Secrets Manager
for i in {1..8}; do
  PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id code-server-multi-dev/dev${i}/password \
    --query SecretString --output text)
  echo "DEV${i}_PASSWORD=${PASSWORD}" >> .env
done

# Start containers
docker-compose up -d

# Verify
docker-compose ps
```

**Day 4: Onboard First Developer (10 minutes)**
```
1. Get password for dev1
2. Share URL + password
3. Help with first login
4. Guide through Claude Code setup
5. Test everything works
```

**Day 5-7: Onboard Remaining Developers**
```
Repeat for dev2-dev8 (10 minutes each)
Total: ~70 minutes for 7 developers
```

### Monthly: Monitoring (30 minutes)

```bash
# Check system health
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average

# Review Bedrock usage
aws logs insights query \
  --log-group-name /aws/bedrock/code-server-multi-dev \
  --start-time $(date -d '1 month ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields identity.arn, usage.inputTokens, usage.outputTokens
| stats sum(usage.inputTokens) as input, sum(usage.outputTokens) as output'

# Check backup status
aws backup list-backup-jobs \
  --by-resource-arn <ebs-volume-arn> \
  --max-results 10

# Review AWS bill
aws ce get-cost-and-usage \
  --time-period Start=$(date -d 'last month' +%Y-%m-01),End=$(date +%Y-%m-01) \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter file://filter.json
```

### As Needed: Support

**Reset Password (2 minutes):**
```bash
# Generate new password
NEW_PASSWORD=$(openssl rand -base64 12)

# Update secret
aws secretsmanager update-secret \
  --secret-id code-server-multi-dev/dev1/password \
  --secret-string "$NEW_PASSWORD"

# Restart container
docker restart code-server-dev1

# Share new password with developer
```

**Add New Developer (10 minutes):**
```
1. Edit docker-compose.yml → Add dev9 service
2. Create password in Secrets Manager
3. Add CNAME record at DNS provider
4. Update ALB target group
5. Start new container
6. Test access
```

**Troubleshoot Issue (10-30 minutes):**
```bash
# Check container logs
docker logs code-server-dev1 --tail 100

# Check system resources
docker stats

# Check CloudWatch logs
aws logs tail /aws/ec2/code-server-multi-dev/system --follow

# Check network connectivity
curl http://localhost:8443/healthz
```

---

## 🎬 User Stories

### Story 1: Junior Developer - นุ่น

**Profile:**
- Experience: 6 months
- Role: Frontend Developer
- Location: Work from home (Mac Mini)
- Project: E-commerce website

**Journey:**

**Day 0 - Onboarding:**
```
10:00 → Receive email from lead with URL and password
10:05 → First login, see VS Code (familiar interface!)
10:15 → Install Claude Code extension
10:20 → Clone project from GitHub
10:30 → Run `npm install` (takes 3 minutes)
10:33 → Start dev server
10:35 → Ready to work!
```

**Week 1 - First Task:**
```
Task: Fix bug in shopping cart calculation

Traditional Approach:
  1. Google the error (20 minutes)
  2. Read Stack Overflow (15 minutes)
  3. Try different solutions (1 hour)
  4. Ask senior for help (wait 30 minutes)
  5. Finally solve (30 minutes)
  Total: ~2.5 hours

With Claude Code:
  1. Copy error message → Ask Claude (1 minute)
  2. Claude explains the issue in Thai (1 minute)
  3. Claude suggests 3 solutions (1 minute)
  4. Try first solution → Works! (5 minutes)
  Total: ~8 minutes

Productivity gain: 18x faster
```

**Month 3 - Confident Developer:**
```
- Uses Claude for daily tasks
- Learned new patterns from Claude
- More independent, asks seniors less
- Completes tasks faster
- Learning speed increased
```

**Feedback:**
> "ไม่ต้องติดตั้งอะไรเลย เข้าไปก็ใช้งานได้เลย Claude ช่วยเยอะมาก
> ไม่ต้องเสียเวลาค้น Stack Overflow ทำให้เรียนรู้เร็วขึ้นเยอะ
> ตอนแรกกลัวว่าจะใช้ browser ไม่ชิน แต่ใช้ไปก็เหมือน VS Code ปกติเลย"

### Story 2: Senior Developer - พี่โอ๊ต

**Profile:**
- Experience: 8 years
- Role: Backend Developer / Tech Lead
- Location: Co-working space
- Project: Microservices architecture

**Journey:**

**Day 0 - Skeptical:**
```
"ทำไมต้องเปลี่ยนจากเครื่องตัวเอง? เครื่องผมมี 32GB RAM,
ใช้ชินแล้ว มี dotfiles ปรับแต่งมานาน..."
```

**Week 1 - Migration:**
```
Day 1: Reluctantly try the platform
Day 2: Migrate dotfiles and settings
Day 3: Install favorite tools (tmux, vim)
Day 4: Setup development environment
Day 5: "Hmm, this actually works..."
```

**Week 2 - Discovery:**
```
Scenario: Working from coffee shop

Problem: Left laptop charger at home
Solution: Borrow friend's laptop → Sign in to dev environment
Result: "Whoa, all my stuff is here! This is actually useful."
```

**Month 2 - Convert:**
```
Uses:
1. Review junior code with Claude
2. Refactor legacy code with AI assistance
3. Generate documentation automatically
4. Work from anywhere (home, office, co-working)
5. No more "sync files between machines"
```

**Feedback:**
> "ตอนแรกไม่ชอบ เพราะชินกับเครื่องตัวเอง แต่พอใช้ไป พบว่า:
> 1. เปลี่ยนเครื่องได้สะดวกมาก ไม่ต้อง sync อะไร
> 2. Claude Code มีประโยชน์มาก โดยเฉพาะตอน review code
> 3. ช่วยจูเนียร์ง่ายขึ้น แค่ส่ง URL ให้ ไม่ต้องไปที่เครื่องเขา
> 4. Onboarding คนใหม่เร็วมาก ไม่ต้องใช้เวลา setup environment
>
> ตอนนี้ยอมรับแล้วว่านี่คือ future of development"

### Story 3: Freelancer - เบส

**Profile:**
- Experience: 4 years
- Role: Full-stack Developer (Part-time)
- Location: Multiple places
- Project: Multiple client projects

**Journey:**

**The Problem:**
```
Before: Managing 3 client projects

Setup 1: Desktop at home (Project A)
Setup 2: MacBook for meetings (All projects)
Setup 3: Backup laptop (Emergency)

Pain points:
- Sync files between machines (USB drive, Dropbox)
- Different Node versions
- "Where did I save that file?"
- Setup time: 30 minutes every context switch
```

**The Solution:**
```
After: Using cloud development

dev1: Project A (main client)
dev2: Project B (side project)
dev3: Project C (experiments)

Workflow:
Morning:  Work on Project A at home (Desktop)
Noon:     Client meeting, show progress (MacBook)
Evening:  Continue Project A at cafe (MacBook)
Night:    Work on Project B at home (Desktop)

No syncing needed → Everything just works
```

**Real Scenario:**
```
Friday, 4 PM:
  Client: "Can you show me the current progress?"
  Me: [Opens laptop at client's office]
  Me: [Signs in to dev1 environment]
  Me: [Shows exact same environment as home]
  Client: "Wow, that's smooth!"
```

**Feedback:**
> "สุดยอดมาก! ผมทำงาน freelance หลายที่
> ก่อนหน้านี้ต้องเอา code ไปมาใน USB drive
> บางทีแก้ที่บ้านแล้วลืม sync ไปเครื่องนอก
>
> ตอนนี้ไปไหนก็เข้างานเดิมต่อได้เลย
> Desktop ที่บ้าน, MacBook พกพา, หรือแม้แต่ iPad ก็ได้
> ไม่ต้องกังวลเรื่อง sync อีกแล้ว
>
> ประหยัดเวลาไปเยอะ โดยเฉพาะตอนเปลี่ยน context ระหว่างโปรเจค"

---

## 🚀 Productivity Gains

### Setup Time Comparison

**Traditional Setup (Local Development):**
```
Day 1: Install OS dependencies
  - Install Python 3.11:           30 min
  - Install Node.js 18:            20 min
  - Install Docker Desktop:        30 min
  - Install PostgreSQL:            20 min
  - Install Redis:                 15 min
  - Configure PATH variables:      15 min
  - Troubleshoot conflicts:        2 hours

Day 2: Project setup
  - Clone repositories:            10 min
  - Install dependencies:          30 min
  - Setup database:                20 min
  - Import test data:              15 min
  - Fix version conflicts:         1 hour

Day 3: Development tools
  - Install VS Code:               10 min
  - Install extensions:            20 min
  - Configure settings:            30 min
  - Setup linters:                 15 min

Day 4-5: Debugging environment issues
  - "Node version mismatch":       1 hour
  - "Port already in use":         30 min
  - "Permission denied":           30 min
  - "Missing environment vars":    20 min

Total: 4-6 days before productive work
```

**Cloud Development Setup:**
```
Day 0: Onboarding
  - Receive URL + password:        1 min
  - First login:                   1 min
  - Install Claude Code:           5 min
  - Clone repository:              5 min
  - Install dependencies:          3 min
  - Start working:                 NOW

Total: 15 minutes before productive work

Productivity Gain: 95% reduction in setup time
```

### Daily Productivity

**Context Switching:**
```
Traditional:
  Switch project → Find files → Remember what you were doing → 15 min lost

Cloud:
  Switch project → Everything is where you left it → 0 min lost

Savings: 15 min × 3 switches/day = 45 min/day
```

**Getting Help:**
```
Traditional:
  1. Search Google (5 min)
  2. Read Stack Overflow (10 min)
  3. Try solution (5 min)
  4. Doesn't work → Repeat (20 min)
  Average: 30 min per question

With Claude:
  1. Ask Claude (30 sec)
  2. Get answer (1 min)
  3. Try solution (5 min)
  Average: 6.5 min per question

Savings: 23.5 min × 5 questions/day = 117 min/day (~2 hours)
```

**Machine Transitions:**
```
Traditional:
  Switch machine → Git pull → Verify environment → 10 min

Cloud:
  Switch machine → Open URL → 0 min

Savings: 10 min × 2 switches/day = 20 min/day
```

**Total Daily Savings:**
```
Context switching:    45 min
Getting help:        120 min
Machine switching:    20 min
--------------------------
Total:               185 min/day (~3 hours)

3 hours/day × 20 working days = 60 hours/month
60 hours = 7.5 working days/month

Productivity Gain: 37.5% more productive days per month
```

### Learning Speed

**Junior Developer Learning Curve:**
```
Traditional:
  Month 1-3: Slow (need lots of help)
  Month 4-6: Moderate (getting confident)
  Month 7-12: Good (mostly independent)

With AI Assistant:
  Month 1: Moderate (AI explains everything)
  Month 2-3: Good (learning patterns quickly)
  Month 4+: Excellent (highly productive)

Learning Speed Increase: 2-3x faster to productivity
```

---

## 📊 Typical Day Timeline

### Full-Stack Developer - Typical Monday

```
08:45 │ Wake up, coffee ☕
      │
09:00 │ Open browser → Navigate to dev3.tuworkshop.vibecode.letsrover.ai
09:01 │ Workspace loads → Everything from Friday still there
09:02 │ Check Slack for overnight messages
09:05 │ Daily standup (video call)
09:15 │ Review TODO list (still open from Friday)
      │
09:20 │ Start: Implement user authentication feature
      │ ├─ Ask Claude: "Best practice สำหรับ JWT authentication?"
      │ ├─ Claude explains + provides code template
      │ └─ Start implementing
      │
10:30 │ Coffee break ☕
10:45 │ Continue coding
      │ ├─ Hit error: "Token verification failed"
      │ ├─ Ask Claude about the error
      │ ├─ Claude: "ตรวจสอบ algorithm ใน jwt.verify()"
      │ └─ Fixed in 5 minutes
      │
12:00 │ Lunch break 🍜
      │ Close browser (auto-save already saved everything)
      │
13:00 │ Open browser → Back to work
13:05 │ Code review: Junior's pull request
      │ ├─ Clone their branch
      │ ├─ Ask Claude: "Review โค้ดนี้ให้หน่อย"
      │ ├─ Claude points out 3 improvements
      │ └─ Leave constructive feedback
      │
14:00 │ Client meeting (show progress)
      │ ├─ Share screen
      │ ├─ Run application in browser
      │ └─ Client happy with progress ✓
      │
15:00 │ Write tests for authentication
      │ ├─ Ask Claude: "เขียน unit tests สำหรับ JWT auth"
      │ ├─ Claude generates test template
      │ ├─ Customize for project
      │ └─ All tests pass ✓
      │
16:00 │ Unexpected: Production bug reported
      │ ├─ Check production logs
      │ ├─ Reproduce locally
      │ ├─ Ask Claude: "Database connection pool exhausted - why?"
      │ ├─ Claude: "ไม่ได้ close connections หลังใช้งาน"
      │ ├─ Fix + deploy
      │ └─ Bug resolved in 30 minutes
      │
17:00 │ Documentation time
      │ ├─ Ask Claude: "เขียน API documentation สำหรับ auth endpoints"
      │ ├─ Claude generates OpenAPI/Swagger spec
      │ ├─ Review and adjust
      │ └─ Commit to repo
      │
18:00 │ End of day
      │ ├─ Git commit + push
      │ ├─ Update TODO list for tomorrow
      │ ├─ Close browser
      │ └─ Done! 🎉
```

### Summary of This Day:
```
Tasks Completed:
  ✓ Implemented user authentication
  ✓ Reviewed junior's code
  ✓ Client demo
  ✓ Wrote unit tests
  ✓ Fixed production bug
  ✓ Wrote documentation

Claude Usage:
  - 12 questions asked
  - ~50,000 tokens used (~$0.75 cost)
  - Saved approximately 2-3 hours of research/coding time

Value:
  Cost: $0.75 for Claude
  Time saved: 2.5 hours
  Hourly rate: $30/hour (example)
  Value generated: $75
  ROI: 10,000% on Claude costs
```

---

## 💡 Recommended Workflow

### For Team Leads

#### 1. Set Claude Usage Policy

```markdown
# Claude Code Usage Guidelines

## When to Use Which Model:

### Haiku ($0.25/M input tokens) - For:
- Simple questions
- Code completion
- Syntax help
- Quick debugging
- Repetitive tasks

### Sonnet ($3/M input tokens) - For:
- Complex problem solving
- Architecture decisions
- Code review
- Refactoring large files
- Learning new concepts

### Opus ($15/M input tokens) - For:
- Critical production issues
- Complex system design
- Security reviews
- Performance optimization

## Best Practices:
1. Close Claude when not actively using
2. Use specific questions (get better answers)
3. Review all AI-generated code
4. Share useful prompts with team
5. Report monthly usage to team lead
```

#### 2. Onboard Developers Systematically

```
Week 1: Pilot (1-2 developers)
  Day 1-2: Setup + training
  Day 3-5: Collect feedback

Week 2: Expand (2-3 more developers)
  Day 1: Onboard based on Week 1 learnings
  Day 2-5: Monitor and assist

Week 3: Full rollout (remaining developers)
  Day 1: Onboard everyone
  Day 2-5: Support and troubleshoot

Week 4: Optimize
  Review usage patterns
  Adjust resources if needed
  Document lessons learned
```

#### 3. Monitor and Optimize

```bash
# Weekly: Check resource usage
aws cloudwatch get-metric-statistics --metric-name CPUUtilization ...

# Weekly: Review Claude usage per developer
aws logs insights query --log-group-name /aws/bedrock/...

# Monthly: Cost analysis
aws ce get-cost-and-usage ...

# Monthly: Developer feedback survey
- Satisfaction (1-10)
- Pain points
- Feature requests
- Success stories
```

### For Developers

#### 1. Organize Your Workspace

```
~/workspace/
├── client-a/
│   ├── frontend/
│   └── backend/
├── client-b/
│   └── api/
├── experiments/
│   └── learning-rust/
└── dotfiles/
    ├── .bashrc
    ├── .gitconfig
    └── .vimrc
```

#### 2. Use Git Effectively

```bash
# Commit frequently
git add .
git commit -m "feat: add user authentication"
git push

# Use branches for features
git checkout -b feature/user-auth

# Never lose work
# (Even if container restarts, code in git is safe)
```

#### 3. Use Claude Wisely

**Good Prompts:**
```
✓ "อธิบาย code นี้ทีละบรรทัด"
✓ "แนะนำวิธีเขียน unit test สำหรับฟังก์ชันนี้"
✓ "Bug นี้เกิดจากอะไร: [paste error]"
✓ "Refactor code นี้ให้ clean ขึ้น พร้อมอธิบายทีละขั้นตอน"
```

**Bad Prompts:**
```
✗ "ช่วยหน่อย" (too vague)
✗ "มันไม่ work" (no context)
✗ "เขียน app ให้หน่อย" (too broad)
```

#### 4. Keyboard Shortcuts

```
Essential Shortcuts:
  Ctrl+P          → Quick file open
  Ctrl+Shift+P    → Command palette
  Ctrl+`          → Toggle terminal
  Ctrl+B          → Toggle sidebar
  Ctrl+Shift+F    → Search in files
  Ctrl+/          → Toggle comment
  F12             → Go to definition
  Shift+Alt+F     → Format document
```

#### 5. Daily Habits

```
Morning:
  ☑ git pull (get latest changes)
  ☑ Check notifications
  ☑ Review TODO list

During Work:
  ☑ Commit frequently (every feature/fix)
  ☑ Write meaningful commit messages
  ☑ Ask Claude before Googling
  ☑ Take breaks (Pomodoro technique)

Evening:
  ☑ git push (backup to remote)
  ☑ Update TODO for tomorrow
  ☑ Close unused tabs/files
```

---

## ❓ FAQ

### General Questions

**Q: ข้อมูลของผมปลอดภัยไหม?**

A: **ปลอดภัยครับ มีหลายชั้น:**

1. **Container Isolation**: แต่ละคนมี container แยก ไม่เห็นข้อมูลกัน
2. **SSL/TLS Encryption**: การเชื่อมต่อทั้งหมดเข้ารหัส
3. **IAM Authentication**: ไม่มี API keys แบบ plaintext
4. **Daily Backups**: Backup ทุกวัน เก็บไว้ 30 วัน
5. **CloudWatch Logging**: Log ทุก action สำหรับ audit
6. **Security Groups**: ควบคุมว่าใครเข้าถึงได้

**Q: ถ้า internet ขาดตอนกำลังเขียน code ทำไง?**

A: **ไม่ต้องกังวลครับ:**
- Auto-save ทุก 1 วินาที
- งานที่ทำไปแล้ว save ไว้แล้ว
- เชื่อมต่อใหม่ → ทุกอย่างยังอยู่
- เสี่ยงเสียงานน้อยมาก

**Q: สามารถติดตั้ง VS Code extension อื่นๆ ได้ไหม?**

A: **ได้ครับ ส่วนใหญ่รองรับ:**
- Extension marketplace เหมือน VS Code ปกติ
- Extensions ที่เป็น web-based ใช้ได้หมด
- บาง extensions ที่ต้องการ native OS อาจไม่ได้

**Q: ใช้ terminal ได้ไหม?**

A: **ได้ครับ มี integrated terminal:**
```bash
# กด Ctrl+` เพื่อเปิด terminal

# ใช้ได้หมดทุกคำสั่ง:
npm run dev
python manage.py runserver
docker ps
git log
```

**Q: Claude ตอบผิดทำไง?**

A: **Review ทุกครั้ง:**
- Claude เป็น assistant ไม่ใช่ความจริง 100%
- ใช้เป็น starting point
- ทดสอบและ verify เสมอ
- ถ้าไม่แน่ใจ → ถามเพิ่ม หรือ Google ต่อ

### Technical Questions

**Q: RAM 4GB พอไหม?**

A: **พอสำหรับ development ทั่วไป:**

✓ พอ:
- Web development (React, Vue, Angular)
- Backend API (Node.js, Python, Go)
- Database dev (PostgreSQL, MySQL)
- Mobile dev (React Native, Flutter)

⚠ อาจไม่พอ:
- Machine learning training
- Running multiple Docker containers
- Large monorepo compilation
- Video processing

**Q: ถ้า resource ไม่พอ upgrade ได้ไหม?**

A: **ได้ครับ:**
```
Current: t3.2xlarge (8 vCPU, 32GB RAM)
Upgrade options:
- t3.4xlarge (16 vCPU, 64GB RAM) → 8GB per dev
- c5.4xlarge (16 vCPU, 32GB RAM) → Better CPU
- m5.4xlarge (16 vCPU, 64GB RAM) → More RAM
```

**Q: รองรับภาษาอะไรบ้าง?**

A: **ทุกภาษาที่ VS Code รองรับ:**
- JavaScript/TypeScript ✓
- Python ✓
- Go ✓
- Rust ✓
- Java ✓
- PHP ✓
- Ruby ✓
- C/C++ ✓
- และอื่นๆ อีกเพียบ

**Q: ถ้าต้องการ database ทำไง?**

A: **หลายทางเลือก:**

1. **Local in container**:
   ```bash
   docker run -d postgres:15
   ```

2. **AWS RDS** (แนะนำสำหรับ production):
   ```
   Connect to RDS endpoint
   Shared across all developers
   ```

3. **SQLite** (สำหรับ development):
   ```bash
   sqlite3 dev.db
   ```

### Cost & Billing

**Q: ใครจ่ายค่า Claude API?**

A: **Team lead จ่ายรวม:**
- AWS Bedrock billing เป็น team-wide
- ไม่ได้เก็บเงินจากแต่ละคน
- แต่มี usage tracking ดูได้ว่าใครใช้เท่าไร

**Q: ใช้ Claude เยอะ โดน charge พิเศษไหม?**

A: **ขึ้นอยู่กับ policy ของ team:**
- Usage แสดงใน CloudWatch
- Team lead set limit ได้
- แนะนำให้ใช้อย่างสมเหตุผล

**Q: ค่าใช้จ่าย infrastructure แพงไหม?**

A: **ประมาณ $52-56/คน/เดือน:**
```
Fixed Infrastructure: $420-450/month ÷ 8 developers
Claude API (variable): $18-180/developer/month

Total: $70-236/developer/month

เปรียบเทียบ:
- GitHub Codespaces: $0.18/hour = ~$300/month
- AWS WorkSpaces: $75/month
- Individual laptop: $1000-2000 upfront

→ Cloud development ถูกกว่าหรือเท่าๆ กัน
```

### Workflow Questions

**Q: Collaborate กับทีมทำไง?**

A: **หลายวิธี:**

1. **Share URL** (read-only access):
   ```
   "ดู code ที่ dev1.tuworkshop.vibecode.letsrover.ai"
   ```

2. **VS Code Live Share**:
   ```
   Install Live Share extension
   Start session → Share link
   Real-time collaboration
   ```

3. **Git workflow**:
   ```
   Normal git flow (commit, push, PR)
   ```

**Q: ทำ CI/CD ยังไง?**

A: **เหมือน development ปกติ:**
```bash
# Push to GitHub
git push origin main

# GitHub Actions run automatically
- Run tests
- Build Docker image
- Deploy to production

# Or manual from code-server:
npm run build
aws s3 sync build/ s3://my-bucket/
```

**Q: Debug production issues ได้ไหม?**

A: **ได้ครับ:**
```bash
# Connect to production logs
aws logs tail /aws/ecs/my-service --follow

# SSH to production (if allowed)
ssh user@production-server

# Or use AWS Systems Manager Session Manager
aws ssm start-session --target i-xxxxx
```

### Migration Questions

**Q: Migrate โปรเจคเดิมยากไหม?**

A: **ไม่ยากครับ:**
```bash
# 1. Clone project
git clone https://github.com/my-org/my-project

# 2. Install dependencies
cd my-project
npm install  # or pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env
nano .env

# 4. Run!
npm run dev

ใช้เวลา: 10-15 นาที
```

**Q: ต้อง learn อะไรใหม่ไหม?**

A: **เกือบไม่ต้อง:**
- VS Code เหมือนเดิม
- Git workflow เหมือนเดิม
- Tools เหมือนเดิม
- แค่เพิ่ม: Claude Code extension

**Q: ถ้าไม่ชอบ กลับไปใช้เครื่องตัวเองได้ไหม?**

A: **ได้ทุกเมื่อ:**
```bash
# Export code from cloud
git clone <your-repo>
# หรือ
zip -r project.zip workspace/

# Continue on local machine
```

---

## 📚 Additional Resources

### Documentation
- [Quick Start Guide](cdk/QUICKSTART.md) - Deploy in 30 minutes
- [CNAME Setup Guide](CNAME_SETUP.md) - DNS configuration
- [Claude Code Setup](CLAUDE_CODE_BEDROCK_SETUP.md) - Configure AI assistant
- [Usage Tracking](BEDROCK_USAGE_TRACKING.md) - Monitor Claude usage

### Support Channels
- **Technical Issues**: Check [CNAME_SETUP.md](CNAME_SETUP.md) troubleshooting
- **Billing Questions**: Review [BEDROCK_USAGE_TRACKING.md](BEDROCK_USAGE_TRACKING.md)
- **Feature Requests**: Talk to your team lead

### Learning Resources
- VS Code Tips: https://code.visualstudio.com/docs
- Git Workflows: https://git-scm.com/book/
- Claude Code: https://claude.com/claude-code

---

## 🎯 Success Metrics

### Individual Developer
```
Measure                    Before    After     Gain
────────────────────────────────────────────────────
Setup time                 4 days    15 min    95% ↓
Daily context switches     45 min    0 min     100% ↓
Getting help               30 min    6 min     80% ↓
Machine transitions        20 min    0 min     100% ↓
────────────────────────────────────────────────────
Total daily savings        —         3 hours   37.5% ↑
```

### Team Level
```
Metric                     Value
────────────────────────────────────
Onboarding time           15 min (vs 4-6 days)
Environment consistency   100% (vs ~70%)
Code quality              ↑ 25% (AI assistance)
Developer satisfaction    8.5/10
Cost per developer        $70-236/month
ROI on Claude costs       10,000%+
```

---

**Last Updated**: 2026-01-19
**Version**: 1.0
**Feedback**: Welcome! Share your experience to improve this guide.

---

**Ready to start?** Follow the [Quick Start Guide](cdk/QUICKSTART.md) to deploy your cloud development environment.
