#!/bin/bash
# Query Claude API usage from CloudWatch

set -e

REGION="ap-southeast-7"
NAMESPACE="CodeServer/ClaudeAPI"
PROJECT="code-server-multi-dev"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Claude API Usage Report"
echo "========================================="
echo ""

# Function to get metric statistics
get_metric_stats() {
    local metric_name=$1
    local developer=$2
    local days=$3

    START_TIME=$(date -u -d "$days days ago" +%Y-%m-%dT%H:%M:%S)
    END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)

    aws cloudwatch get-metric-statistics \
        --namespace "$NAMESPACE" \
        --metric-name "$metric_name" \
        --dimensions Name=Developer,Value="$developer" Name=Project,Value="$PROJECT" \
        --start-time "$START_TIME" \
        --end-time "$END_TIME" \
        --period 86400 \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text
}

# Function to get total cost for a developer
get_developer_cost() {
    local developer=$1
    local days=$2

    START_TIME=$(date -u -d "$days days ago" +%Y-%m-%dT%H:%M:%S)
    END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)

    aws cloudwatch get-metric-statistics \
        --namespace "$NAMESPACE" \
        --metric-name "TotalCost" \
        --dimensions Name=Developer,Value="$developer" Name=Project,Value="$PROJECT" \
        --start-time "$START_TIME" \
        --end-time "$END_TIME" \
        --period $((86400 * days)) \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text
}

# Query time period (default: last 30 days)
DAYS=${1:-30}

echo "Period: Last $DAYS days"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "%-12s %-15s %-15s %-15s %-12s\n" "Developer" "Input Tokens" "Output Tokens" "Total Tokens" "Cost (USD)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_INPUT=0
TOTAL_OUTPUT=0
TOTAL_COST=0

for i in {1..8}; do
    DEVELOPER="dev$i"

    INPUT=$(get_metric_stats "InputTokens" "$DEVELOPER" "$DAYS")
    OUTPUT=$(get_metric_stats "OutputTokens" "$DEVELOPER" "$DAYS")
    COST=$(get_developer_cost "$DEVELOPER" "$DAYS")

    # Handle None/null values
    INPUT=${INPUT:-0}
    OUTPUT=${OUTPUT:-0}
    COST=${COST:-0}

    # Convert to integers for display (remove decimals)
    INPUT_INT=$(printf "%.0f" "$INPUT" 2>/dev/null || echo "0")
    OUTPUT_INT=$(printf "%.0f" "$OUTPUT" 2>/dev/null || echo "0")
    TOTAL_TOKENS=$((INPUT_INT + OUTPUT_INT))
    COST_FORMATTED=$(printf "%.2f" "$COST" 2>/dev/null || echo "0.00")

    # Add to totals
    TOTAL_INPUT=$((TOTAL_INPUT + INPUT_INT))
    TOTAL_OUTPUT=$((TOTAL_OUTPUT + OUTPUT_INT))
    TOTAL_COST=$(echo "$TOTAL_COST + $COST" | bc -l)

    # Color coding based on usage
    if [ "$TOTAL_TOKENS" -gt 1000000 ]; then
        COLOR=$YELLOW
    elif [ "$TOTAL_TOKENS" -gt 100000 ]; then
        COLOR=$BLUE
    else
        COLOR=$GREEN
    fi

    printf "${COLOR}%-12s${NC} %'15d %'15d %'15d \$%-11.2f\n" \
        "$DEVELOPER" "$INPUT_INT" "$OUTPUT_INT" "$TOTAL_TOKENS" "$COST_FORMATTED"
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "%-12s %'15d %'15d %'15d \$%-11.2f\n" \
    "TOTAL" "$TOTAL_INPUT" "$TOTAL_OUTPUT" "$((TOTAL_INPUT + TOTAL_OUTPUT))" "$TOTAL_COST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Calculate monthly projection
DAYS_IN_MONTH=30
if [ "$DAYS" -lt "$DAYS_IN_MONTH" ]; then
    MONTHLY_PROJECTION=$(echo "$TOTAL_COST * $DAYS_IN_MONTH / $DAYS" | bc -l)
    printf "Monthly Projection: \$%.2f\n" "$MONTHLY_PROJECTION"
    echo ""
fi

# Show top users
echo "Top 3 Users:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get detailed logs for sorting (simplified - in production use proper sorting)
for i in {1..8}; do
    DEVELOPER="dev$i"
    COST=$(get_developer_cost "$DEVELOPER" "$DAYS")
    COST=${COST:-0}
    echo "$DEVELOPER $COST"
done | sort -k2 -rn | head -3 | while read dev cost; do
    printf "${YELLOW}%-12s${NC} \$%.2f\n" "$dev" "$cost"
done

echo ""
echo "========================================="
echo "Usage: $0 [days]"
echo "Example: $0 7  (last 7 days)"
echo "========================================="
