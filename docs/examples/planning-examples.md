# Planning Layer - Usage Examples

Complete examples demonstrating the Forge conversational planning system.

## Table of Contents

1. [Basic Planning Session](#basic-planning-session)
2. [CLI Usage Examples](#cli-usage-examples)
3. [Python API Usage](#python-api-usage)
4. [Real-world Planning Scenarios](#real-world-planning-scenarios)
5. [Session Management](#session-management)
6. [Integration Examples](#integration-examples)

---

## Basic Planning Session

### Simple API Project

```bash
$ export ANTHROPIC_API_KEY='your-api-key'
$ forge chat

⚒ Forge v1.0.0 - AI Development Orchestration

I'll help you plan your software project through conversation.

Commands:
  • Type your project ideas or answer my questions
  • done - Finish planning and create project
  • save - Save conversation progress
  • help - Show this help
  • clear - Clear screen
  • exit - Cancel session

Let's start planning! What would you like to build?

You: I want to build a REST API for managing recipes

Forge: Great idea! A recipe management API. Let me understand this better:

**Key Questions:**
- What operations will users need? (creating recipes, searching, editing, etc.)
- Do you need user authentication and personal recipe collections?

You: Yes, users should have accounts and private recipe collections. They can create, edit, delete, and search their recipes. Also share recipes publicly.

Forge: Perfect! So we're looking at:

**Core Features:**
• User authentication and profiles
• Personal recipe collections
• CRUD operations for recipes
• Recipe search functionality
• Public recipe sharing

**Questions:**
- Any preference for tech stack? (Python, Node.js, etc.)
- Database preferences?
- Deployment environment?

You: Python with FastAPI. PostgreSQL database. Deploy to AWS.

Forge: Excellent choices!

**Summary so far:**
📱 **Project**: Recipe Management API
🔧 **Stack**: Python + FastAPI + PostgreSQL
☁️ **Deploy**: AWS

A few more details:
- Any specific features for recipes? (ingredients, steps, photos, ratings?)
- Performance requirements? (expected user count?)

You: Recipes should have ingredients lists, cooking steps, photos, and user ratings. Expect around 10,000 users initially.

Forge: Perfect! I have everything I need. Type 'done' when you're ready to create the project.

You: done

Analyzing conversation...
Extracting requirements...

══════════════════════════════════════
          Project Summary
══════════════════════════════════════

Project: Recipe Management API
Description: REST API for managing user recipes with authentication and sharing

Requirements:
  • User authentication system
  • User profile management
  • Recipe CRUD operations
  • Recipe search functionality
  • Public recipe sharing
  • Image upload and storage
  • Rating system

Features:
  • Personal recipe collections
  • Ingredient management
  • Cooking step instructions
  • Photo uploads
  • User ratings and reviews
  • Public recipe discovery

Technology Stack:
  Python, FastAPI, PostgreSQL, AWS

Constraints:
  • Must support 10,000 initial users
  • AWS deployment required

Success Criteria:
  • Support 10,000 concurrent users
  • Secure authentication
  • Fast search performance

Deployment: AWS
Target Users: Home cooks managing and sharing recipes

Create Forge project from this plan? (y/n): y

✓ Created project: recipe-management-api-20251207
✓ Conversation saved to: .forge/sessions/planning-recipe-management-api-20251207.json

✓ Planning session completed successfully!
```

---

## CLI Usage Examples

### Starting a New Planning Session

```bash
# Basic usage
forge chat

# With environment variable
ANTHROPIC_API_KEY='sk-ant-...' forge chat
```

### Resuming a Previous Session

```bash
# Resume by project ID
forge chat --project-id recipe-management-api-20251207

# Or with short flag
forge chat -p my-project-20251207
```

### Special Commands During Chat

```bash
You: save
✓ Conversation saved to: .forge/sessions/planning-20251207-143022.json

You: help
Available Commands
┌──────────────┬─────────────────────────────────────────────┐
│ Command      │ Description                                 │
├──────────────┼─────────────────────────────────────────────┤
│ done/finish  │ Complete planning and extract requirements  │
│ save         │ Save current conversation progress          │
│ help         │ Show this help message                      │
│ clear        │ Clear the screen                            │
│ exit/quit    │ Cancel and exit session                     │
└──────────────┴─────────────────────────────────────────────┘

You: clear
# Screen clears and shows welcome banner again

You: exit
Exit without finishing? (y/n): y
Session cancelled.
```

---

## Python API Usage

### Basic PlanningAgent Usage

```python
import asyncio
from forge.layers.planning import PlanningAgent

async def main():
    # Initialize agent
    agent = PlanningAgent(api_key="your-api-key")

    # Send message and stream response
    print("User: I want to build a todo app")
    print("Forge: ", end="")

    async for chunk in agent.chat("I want to build a todo app"):
        print(chunk, end="", flush=True)

    print("\n")

    # Continue conversation
    print("User: Use Python and React")
    print("Forge: ", end="")

    async for chunk in agent.chat("Use Python and React"):
        print(chunk, end="", flush=True)

    print("\n")

    # Get project summary
    summary = agent.get_project_summary()
    print("\nProject Summary:")
    print(f"Name: {summary['project_name']}")
    print(f"Tech Stack: {', '.join(summary['tech_stack'])}")

asyncio.run(main())
```

### Session Management

```python
from forge.layers.planning import PlanningAgent
from pathlib import Path

# Initialize agent
agent = PlanningAgent(api_key="your-api-key")

# Have a conversation
async def plan_project():
    async for chunk in agent.chat("I want to build a blog platform"):
        print(chunk, end="")

    async for chunk in agent.chat("Use Django and PostgreSQL"):
        print(chunk, end="")

    # Save session
    session_path = Path(".forge/sessions/blog-planning.json")
    session_path.parent.mkdir(parents=True, exist_ok=True)
    agent.save_conversation(str(session_path))
    print(f"Saved to {session_path}")

# Later, resume the session
def resume_planning():
    agent = PlanningAgent(api_key="your-api-key")
    agent.load_conversation(".forge/sessions/blog-planning.json")

    print(f"Resumed conversation with {agent.get_conversation_length()} messages")
    print(f"Last message: {agent.get_last_assistant_message()[:100]}...")

asyncio.run(plan_project())
```

### Custom Model Selection

```python
from forge.layers.planning import PlanningAgent

# Use Claude Opus for more complex planning
agent = PlanningAgent(
    api_key="your-api-key",
    model="claude-opus-4-20250514"
)

# Use Haiku for simpler, faster planning
agent = PlanningAgent(
    api_key="your-api-key",
    model="claude-haiku-4-20250514"
)
```

### Error Handling

```python
from forge.layers.planning import PlanningAgent, PlanningError
import asyncio

async def safe_planning():
    try:
        agent = PlanningAgent(api_key="your-api-key")

        async for chunk in agent.chat("Build an e-commerce platform"):
            print(chunk, end="")

    except PlanningError as e:
        print(f"Planning error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(safe_planning())
```

---

## Real-world Planning Scenarios

### Scenario 1: Mobile App Backend

```
You: I need a backend for a fitness tracking mobile app

Forge: Great! A fitness tracking backend. Let me understand the requirements:

**Key Questions:**
- What fitness data will you track? (workouts, nutrition, goals, etc.)
- Do you need real-time sync across devices?
- Any integration with wearables or health APIs?

You: Track workouts, nutrition logs, and fitness goals. Yes, real-time sync needed. Integrate with Apple Health and Google Fit.

Forge: Perfect! Here's what I understand:

**Core Features:**
• Workout tracking and logging
• Nutrition/calorie logging
• Fitness goal management
• Real-time device sync
• Health API integrations (Apple Health, Google Fit)

**Questions:**
- Tech stack preferences?
- Expected user scale?
- Any specific security/compliance needs (HIPAA, GDPR)?

You: Node.js backend. Expect 50,000 users in first year. Need GDPR compliance for EU users.

Forge: Excellent. A few more details:

**Current Stack:**
🔧 Node.js backend
👥 50,000 users (first year)
🔒 GDPR compliance required

**Final Questions:**
- Database choice? (MongoDB, PostgreSQL, etc.)
- Deployment platform? (AWS, GCP, Azure?)
- Real-time tech preference? (WebSockets, Server-Sent Events?)

You: MongoDB for flexibility. Deploy on AWS. Use WebSockets for real-time updates.

Forge: Perfect! I have a complete picture. Type 'done' to create the project.

You: done

[Project summary would show complete requirements with all details]
```

**Extracted Summary:**
```json
{
  "project_name": "Fitness Tracker Backend",
  "description": "Backend API for mobile fitness tracking with real-time sync",
  "requirements": [
    "Workout tracking system",
    "Nutrition logging",
    "Goal management",
    "Real-time device synchronization",
    "Apple Health integration",
    "Google Fit integration",
    "GDPR compliance"
  ],
  "tech_stack": ["Node.js", "MongoDB", "WebSockets", "AWS"],
  "constraints": [
    "GDPR compliance for EU users",
    "Must support 50,000 users in first year"
  ],
  "deployment": "AWS"
}
```

### Scenario 2: Enterprise Dashboard

```
You: We need an analytics dashboard for our enterprise SaaS platform

Forge: An enterprise analytics dashboard - excellent! Let me gather the details:

**Understanding the Scope:**
- What metrics and data will the dashboard display?
- Who are the users? (executives, analysts, customers?)
- Any existing systems to integrate with?

You: Display user engagement, revenue metrics, system performance, and feature adoption. Used by our product managers and executives. Needs to integrate with our PostgreSQL database and Stripe API.

Forge: Great context! So we have:

**Dashboard Features:**
• User engagement analytics
• Revenue metrics and trends
• System performance monitoring
• Feature adoption tracking

**Integrations:**
• PostgreSQL (existing database)
• Stripe API (payment data)

**Questions:**
- Frontend framework preference? (React, Vue, Angular?)
- Real-time updates needed or batch refresh?
- Authentication method? (SSO, OAuth, etc.)

You: React with TypeScript. Real-time updates for performance metrics, hourly refresh for others. Use our existing OAuth2 SSO.

Forge: Perfect! A few more details:

- Any specific charting library? (D3, Chart.js, Recharts?)
- Backend API needed or direct database queries?
- Performance requirements? (expected concurrent users?)

You: Use Recharts for simplicity. Need a Node.js backend API, no direct database access from frontend. Expect 100 concurrent users max.

Forge: Excellent! I have everything needed. Type 'done' when ready.

You: done
```

### Scenario 3: Microservices Migration

```
You: Help me plan migrating our monolithic app to microservices

Forge: A microservices migration - that's a significant undertaking! Let's plan this carefully:

**Understanding the Context:**
- What does your current monolith do? (domain/purpose)
- What's driving the migration? (scale, team size, deployment flexibility?)
- Any specific pain points with the current architecture?

You: It's an e-commerce platform. We have scaling issues during peak sales, and our growing team (40 developers) struggles with deployment conflicts. Biggest pain is that the checkout process blocks other deployments.

Forge: Those are excellent reasons for microservices. Let's break this down:

**Current Challenges:**
• Scaling bottlenecks during peak traffic
• 40-developer team with deployment conflicts
• Checkout process blocks deployments

**Key Questions:**
- Which services do you want to extract first? (checkout, user management, inventory, etc.)
- Current tech stack?
- Container/orchestration platform? (Kubernetes, Docker Swarm, ECS?)

You: Start with checkout and inventory services - those are most critical. Current stack is Python Django monolith with PostgreSQL. Want to use Kubernetes on AWS.

Forge: Smart prioritization! More details:

**Migration Plan:**
• Phase 1: Checkout service
• Phase 2: Inventory service
• Platform: Kubernetes on AWS
• Current: Django + PostgreSQL

**Questions:**
- Keep Python for new services or explore other languages?
- Database strategy? (shared DB, database per service, or hybrid?)
- API gateway needed? (Kong, AWS API Gateway, etc.)

You: Keep Python, use FastAPI for services. Database per service for checkout and inventory. Use AWS API Gateway.

Forge: Perfect! Last questions:

- Event-driven communication needed? (message queue/event bus?)
- Monitoring and observability tools? (Prometheus, Datadog, etc.)
- Timeline constraints?

You: Yes, use RabbitMQ for async communication. Datadog for monitoring. Need checkout service live in 3 months.

Forge: Excellent! I have a complete migration plan. Type 'done' to create the project.

You: done
```

---

## Session Management

### Saving Sessions at Different Points

```bash
# Save after initial discussion
You: I want to build a social network for book clubs
Forge: [responds with questions]
You: save
✓ Conversation saved to: .forge/sessions/planning-20251207-100530.json

# Continue planning later
$ forge chat  # New session
You: [different project]

# Or resume the book club project
$ forge chat -p planning-20251207-100530
Resumed conversation for project: planning-20251207-100530
You: [continue where you left off]
```

### Programmatic Session Management

```python
from forge.layers.planning import PlanningAgent
from datetime import datetime
import json

class PlanningSession:
    def __init__(self, api_key: str, session_id: str = None):
        self.agent = PlanningAgent(api_key)
        self.session_id = session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.session_path = f".forge/sessions/{self.session_id}.json"

        # Load existing session if provided
        if session_id:
            try:
                self.agent.load_conversation(self.session_path)
                print(f"Loaded session: {session_id}")
            except:
                print(f"Starting new session: {session_id}")

    async def chat(self, message: str):
        """Send message and get response"""
        response = ""
        async for chunk in self.agent.chat(message):
            print(chunk, end="", flush=True)
            response += chunk
        print()
        return response

    def save(self):
        """Save current session"""
        self.agent.save_conversation(self.session_path)
        print(f"Saved: {self.session_path}")

    def get_summary(self):
        """Get project summary from conversation"""
        return self.agent.get_project_summary()

    def export_markdown(self, filepath: str):
        """Export conversation as markdown"""
        lines = ["# Planning Session\n"]
        lines.append(f"**Session ID:** {self.session_id}\n")
        lines.append(f"**Date:** {datetime.now().isoformat()}\n\n")

        for msg in self.agent.conversation_history:
            role = "**You:**" if msg["role"] == "user" else "**Forge:**"
            lines.append(f"{role} {msg['content']}\n\n")

        Path(filepath).write_text("\n".join(lines))

# Usage
async def main():
    # Start new session
    session = PlanningSession(api_key="your-key")
    await session.chat("I want to build a podcast hosting platform")
    session.save()

    # Resume later
    session2 = PlanningSession(api_key="your-key", session_id=session.session_id)
    await session2.chat("Use Ruby on Rails")
    summary = session2.get_summary()
    session2.export_markdown("podcast-platform-plan.md")
```

---

## Integration Examples

### Integration with State Manager

```python
from forge.layers.planning import PlanningAgent
from forge.core.state_manager import StateManager
import asyncio
import re
from datetime import datetime

async def plan_and_create_project(api_key: str):
    """Complete workflow: plan conversation → create project"""

    # Planning phase
    agent = PlanningAgent(api_key)

    print("Let's plan your project!\n")

    # Simulated conversation
    await agent.chat("I want to build a task management API")
    await agent.chat("Use Python FastAPI and PostgreSQL")
    await agent.chat("Deploy to AWS, need 1000 users support")

    # Extract summary
    summary = agent.get_project_summary()

    # Create project in Forge
    state = StateManager()

    # Generate project ID
    project_name = summary.get("project_name", "planned-project")
    slug = re.sub(r'[^\w\s-]', '', project_name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    timestamp = datetime.now().strftime("%Y%m%d")
    project_id = f"{slug}-{timestamp}"

    # Create project
    project = state.create_project(
        project_id=project_id,
        name=project_name,
        description=summary.get("description", ""),
        metadata={
            "planning_summary": summary,
            "created_from": "planning_session",
            "tech_stack": summary.get("tech_stack", []),
            "requirements": summary.get("requirements", [])
        }
    )

    # Create checkpoint
    state.checkpoint(
        project_id=project_id,
        stage="planning",
        state={"summary": summary},
        description="Planning session completed"
    )

    # Save conversation
    agent.save_conversation(f".forge/sessions/planning-{project_id}.json")

    print(f"\n✓ Created project: {project_id}")
    print(f"✓ Requirements: {len(summary.get('requirements', []))}")
    print(f"✓ Tech stack: {', '.join(summary.get('tech_stack', []))}")

    state.close()
    return project

asyncio.run(plan_and_create_project("your-api-key"))
```

### Integration with Custom UI

```python
from forge.layers.planning import PlanningAgent
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import asyncio

class CustomPlanningUI:
    def __init__(self, api_key: str):
        self.agent = PlanningAgent(api_key)
        self.console = Console()

    async def run(self):
        """Run custom planning interface"""

        # Welcome
        self.console.print(Panel(
            "[bold blue]Custom Planning Interface[/bold blue]\n"
            "Let's build something amazing!",
            border_style="blue"
        ))

        # Collect messages
        messages = [
            "I want to build a blog platform",
            "Use Next.js and Prisma",
            "Deploy to Vercel"
        ]

        for msg in messages:
            self.console.print(f"\n[cyan]You:[/cyan] {msg}")
            self.console.print("[green]Forge:[/green] ", end="")

            async for chunk in self.agent.chat(msg):
                self.console.print(chunk, end="")

            self.console.print()

        # Extract with progress
        with Progress() as progress:
            task = progress.add_task("[cyan]Analyzing conversation...", total=100)

            summary = self.agent.get_project_summary()

            progress.update(task, completed=100)

        # Display results
        self.console.print(Panel(
            f"[bold]Project:[/bold] {summary['project_name']}\n"
            f"[bold]Stack:[/bold] {', '.join(summary['tech_stack'])}\n"
            f"[bold]Requirements:[/bold] {len(summary['requirements'])}",
            title="Summary",
            border_style="green"
        ))

        return summary

# Run it
async def main():
    ui = CustomPlanningUI(api_key="your-key")
    summary = await ui.run()

asyncio.run(main())
```

### Batch Planning for Multiple Projects

```python
from forge.layers.planning import PlanningAgent
import asyncio

async def batch_plan_projects(api_key: str, project_ideas: list):
    """Plan multiple projects in sequence"""

    summaries = []

    for idea in project_ideas:
        agent = PlanningAgent(api_key)

        print(f"\n{'='*60}")
        print(f"Planning: {idea['name']}")
        print(f"{'='*60}\n")

        # Send all messages for this project
        for msg in idea['messages']:
            print(f"You: {msg}")
            async for chunk in agent.chat(msg):
                print(chunk, end="")
            print("\n")

        # Get summary
        summary = agent.get_project_summary()
        summaries.append(summary)

        # Save
        agent.save_conversation(f".forge/sessions/{idea['name']}.json")

        print(f"✓ Completed: {idea['name']}\n")

    return summaries

# Usage
projects = [
    {
        "name": "todo-api",
        "messages": [
            "Build a todo list API",
            "Use Python FastAPI",
            "PostgreSQL database"
        ]
    },
    {
        "name": "blog-platform",
        "messages": [
            "Build a blogging platform",
            "Use Ruby on Rails",
            "Deploy to Heroku"
        ]
    }
]

asyncio.run(batch_plan_projects("your-key", projects))
```

---

## Advanced Usage Patterns

### Conversation Analysis

```python
from forge.layers.planning import PlanningAgent

def analyze_conversation(agent: PlanningAgent):
    """Analyze conversation metrics"""

    metrics = {
        "total_messages": agent.get_conversation_length(),
        "user_messages": sum(1 for msg in agent.conversation_history if msg["role"] == "user"),
        "assistant_messages": sum(1 for msg in agent.conversation_history if msg["role"] == "assistant"),
        "turns": agent.session_metadata["turns"],
        "started_at": agent.session_metadata["started_at"],
        "avg_user_length": 0,
        "avg_assistant_length": 0
    }

    user_lengths = [len(msg["content"]) for msg in agent.conversation_history if msg["role"] == "user"]
    assistant_lengths = [len(msg["content"]) for msg in agent.conversation_history if msg["role"] == "assistant"]

    if user_lengths:
        metrics["avg_user_length"] = sum(user_lengths) / len(user_lengths)
    if assistant_lengths:
        metrics["avg_assistant_length"] = sum(assistant_lengths) / len(assistant_lengths)

    return metrics

# Usage
agent = PlanningAgent(api_key="your-key")
# ... have conversation ...
metrics = analyze_conversation(agent)
print(f"Conversation had {metrics['turns']} turns")
print(f"Average user message: {metrics['avg_user_length']:.0f} characters")
```

### Custom Extraction Logic

```python
from forge.layers.planning import PlanningAgent
import re

class EnhancedPlanningAgent(PlanningAgent):
    """Extended agent with custom extraction"""

    def extract_tech_stack_detailed(self) -> dict:
        """Extract detailed tech stack categorization"""

        conversation_text = self._format_conversation().lower()

        categories = {
            "languages": ["python", "javascript", "typescript", "ruby", "go", "java"],
            "frameworks": ["django", "flask", "fastapi", "react", "vue", "angular", "rails"],
            "databases": ["postgresql", "mysql", "mongodb", "redis", "dynamodb"],
            "cloud": ["aws", "gcp", "azure", "heroku", "vercel", "netlify"],
            "tools": ["docker", "kubernetes", "terraform", "github actions"]
        }

        detected = {category: [] for category in categories}

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in conversation_text:
                    detected[category].append(keyword)

        return detected

    def get_complexity_estimate(self) -> str:
        """Estimate project complexity from requirements"""

        summary = self.get_project_summary()

        req_count = len(summary.get("requirements", []))
        tech_count = len(summary.get("tech_stack", []))

        score = req_count + (tech_count * 2)

        if score < 5:
            return "simple"
        elif score < 15:
            return "moderate"
        else:
            return "complex"

# Usage
agent = EnhancedPlanningAgent(api_key="your-key")
# ... conversation ...
tech_stack = agent.extract_tech_stack_detailed()
complexity = agent.get_complexity_estimate()
print(f"Complexity: {complexity}")
print(f"Languages: {tech_stack['languages']}")
```

---

## Best Practices

### 1. Effective Conversation Flow

```python
# ✅ GOOD: Progressive detail gathering
messages = [
    "I want to build a social media platform",  # High level
    "Focus on photo sharing with filters",       # Specific feature
    "Use React Native for mobile apps",          # Tech choice
    "Need 100k users support in first year"     # Scale requirement
]

# ❌ BAD: All details at once
message = "I want to build a social media platform with photo sharing, filters, React Native, supporting 100k users, using AWS, with Redis caching..."
```

### 2. Save Sessions Regularly

```python
async def plan_with_checkpoints(agent, messages):
    """Save after each major decision point"""

    for i, msg in enumerate(messages):
        async for chunk in agent.chat(msg):
            print(chunk, end="")

        # Save after every 3 messages
        if (i + 1) % 3 == 0:
            agent.save_conversation(f".forge/sessions/checkpoint-{i+1}.json")
```

### 3. Validate Extracted Requirements

```python
def validate_summary(summary: dict) -> list:
    """Validate completeness of extracted summary"""

    issues = []

    required_fields = ["project_name", "description", "tech_stack", "requirements"]
    for field in required_fields:
        if not summary.get(field):
            issues.append(f"Missing {field}")

    if len(summary.get("requirements", [])) < 3:
        issues.append("Too few requirements (minimum 3 recommended)")

    if len(summary.get("tech_stack", [])) == 0:
        issues.append("No technology stack specified")

    return issues

# Usage
summary = agent.get_project_summary()
issues = validate_summary(summary)
if issues:
    print("⚠️  Summary validation issues:")
    for issue in issues:
        print(f"  - {issue}")
```

---

## Troubleshooting

### Common Issues

**Issue: Empty or incomplete summary extraction**

```python
# Check conversation length
if agent.get_conversation_length() < 4:
    print("⚠️  Too few messages for good extraction (minimum 4 recommended)")

# Verify last messages
print(f"Last user: {agent.get_last_user_message()}")
print(f"Last assistant: {agent.get_last_assistant_message()}")
```

**Issue: Session file not found when resuming**

```python
from pathlib import Path

session_path = Path(f".forge/sessions/planning-{project_id}.json")
if not session_path.exists():
    print(f"❌ Session file not found: {session_path}")
    print(f"Available sessions:")
    for session in Path(".forge/sessions").glob("*.json"):
        print(f"  - {session.name}")
```

**Issue: API rate limiting**

```python
import time

async def chat_with_rate_limit(agent, messages, delay=1.0):
    """Add delay between messages to avoid rate limits"""

    for msg in messages:
        async for chunk in agent.chat(msg):
            print(chunk, end="")

        time.sleep(delay)  # Wait between requests
```

---

This completes the planning layer usage examples!
