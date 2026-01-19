#!/bin/bash
# Helper script for switching between projects
# Usage: ./switch-project.sh <project-name>

PROJECT_NAME=$1

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: ./switch-project.sh <project-name>"
    echo ""
    echo "Available projects in workspace:"
    ls -d ~/workspace/*/ 2>/dev/null | xargs -n 1 basename || echo "  (no projects found)"
    exit 1
fi

PROJECT_DIR="$HOME/workspace/$PROJECT_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project '$PROJECT_NAME' not found in ~/workspace/"
    echo ""
    echo "Available projects:"
    ls -d ~/workspace/*/ 2>/dev/null | xargs -n 1 basename || echo "  (no projects found)"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

echo "========================================"
echo "Switched to: $PROJECT_NAME"
echo "========================================"
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# Show git status if it's a git repo
if [ -d .git ]; then
    echo "Git status:"
    git status -sb
    echo ""
fi

# Check for package.json
if [ -f package.json ]; then
    echo "Node.js project detected"
    echo "Available scripts:"
    cat package.json | jq -r '.scripts | to_entries[] | "  npm run \(.key)"' 2>/dev/null || echo "  (install jq to see scripts)"
    echo ""
fi

# Check for Python files
if [ -f requirements.txt ] || [ -f pyproject.toml ] || [ -f setup.py ]; then
    echo "Python project detected"
    if [ -f requirements.txt ]; then
        echo "  requirements.txt found"
    fi
    if [ -d venv ]; then
        echo "  Virtual environment: venv/ (run: source venv/bin/activate)"
    fi
    echo ""
fi

# Check for running processes on common ports
echo "Checking for running dev servers..."
RUNNING_PORTS=$(netstat -tuln 2>/dev/null | grep LISTEN | grep -E ":(3000|3001|4000|8000)" | awk '{print $4}' | cut -d: -f2 | sort -u)

if [ -n "$RUNNING_PORTS" ]; then
    echo "Active dev server ports:"
    echo "$RUNNING_PORTS" | while read port; do
        echo "  Port $port is in use"
    done
else
    echo "  No dev servers running"
fi

echo ""
echo "========================================"
echo "Ready to work on $PROJECT_NAME!"
echo "========================================"

# Start or attach tmux session
if command -v tmux &> /dev/null; then
    SESSION_NAME="$PROJECT_NAME"

    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo ""
        echo "Attaching to existing tmux session '$SESSION_NAME'..."
        echo "(Press Ctrl+B then D to detach)"
        sleep 1
        tmux attach-session -t "$SESSION_NAME"
    else
        echo ""
        echo "Would you like to start a tmux session for this project? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Creating tmux session '$SESSION_NAME'..."
            echo "(Press Ctrl+B then D to detach)"
            sleep 1
            tmux new-session -s "$SESSION_NAME" -c "$PROJECT_DIR"
        fi
    fi
fi
