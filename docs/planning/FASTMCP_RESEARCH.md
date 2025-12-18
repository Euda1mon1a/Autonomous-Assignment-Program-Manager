# FastMCP Research Document

## Table of Contents
1. [What is FastMCP](#what-is-fastmcp)
2. [Installation and Setup](#installation-and-setup)
3. [Core Concepts](#core-concepts)
4. [Code Examples](#code-examples)
5. [FastAPI Integration](#fastapi-integration)
6. [Testing MCP Servers](#testing-mcp-servers)
7. [Deployment Considerations](#deployment-considerations)
8. [Relevance to Scheduling Domain](#relevance-to-scheduling-domain)

---

## What is FastMCP

FastMCP is an open-source Python framework designed to make building Model Context Protocol (MCP) servers and clients both simple and efficient. It provides the fast, Pythonic way to build MCP servers and clients using high-level abstractions.

### Key Features

- **Simple API**: With just a few decorators, you can transform ordinary Python functions into MCP resources and tools that any MCP-compatible client (like Claude Desktop) can instantly use.
- **Production-Ready**: FastMCP 2.0 delivers everything needed for production:
  - Advanced MCP patterns (server composition, proxying, OpenAPI/FastAPI generation, tool transformation)
  - Enterprise authentication (Google, GitHub, Azure, Auth0, WorkOS)
  - Deployment tools
  - Testing frameworks
  - Comprehensive client libraries
- **ASGI-Compatible**: Built on Starlette, allowing easy integration with other ASGI-compatible frameworks like FastAPI
- **Multiple Transports**: Supports stdio, HTTP, and SSE (Server-Sent Events) transports

### MCP Protocol Overview

The Model Context Protocol (MCP) is often described as **"the USB-C port for AI"** - it provides a uniform way to connect LLMs to resources they can use. MCP servers expose data and functionality to LLM applications in a secure, standardized way.

### FastMCP Evolution

- **FastMCP 1.0**: Pioneered Python MCP development and was incorporated into the official MCP SDK in 2024
- **FastMCP 2.0**: The actively maintained version that extends far beyond basic protocol implementation

---

## Installation and Setup

### Requirements
- Python 3.10 or higher

### Installation

```bash
pip install fastmcp
```

### Creating Your First Server

Create a new file called `my_server.py`:

```python
from fastmcp import FastMCP

# Instantiate the FastMCP server
mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    """Returns a greeting message."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

### Running the Server

**Stdio Transport (Traditional)**
```bash
python my_server.py
```

**HTTP Transport (Web-based)**
```python
mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
```

**SSE Transport**
```python
mcp.run(transport="sse", host="127.0.0.1", port=8000)
```

---

## Core Concepts

The Model Context Protocol provides three main primitives:

### 1. Resources (Read-Only Data Exposure)

**Resources** are data entities that your server exposes. They provide context or information that clients can read and use.

**Key Characteristics:**
- Similar to GET endpoints in a REST API
- Provide data without performing significant computation or side effects
- Application-driven (host applications determine how to incorporate context)
- Can be static (configuration, constants) or dynamic (user profiles, database records)

**Use Cases:**
- Exposing configuration data
- Providing database records
- Offering file contents
- Sharing cached data or metadata

### 2. Tools (Callable Functions)

**Tools** are executable functions that perform actions or computations.

**Key Characteristics:**
- Similar to POST/PUT/DELETE endpoints in a REST API
- Model-controlled (LLM can discover and invoke tools automatically)
- Can perform computations, API calls, or side effects
- Schema auto-generated from type hints and docstrings

**Use Cases:**
- Performing calculations
- Making external API calls
- Database mutations
- File operations
- Any action that changes state

### 3. Prompts (Reusable Templates)

**Prompts** are reusable templates that guide AI interactions.

**Key Characteristics:**
- Structure how an AI model asks questions or explains concepts
- Can include parameters for customization
- Help maintain consistent interaction patterns

**Use Cases:**
- Standardizing query patterns
- Creating reusable conversation templates
- Guiding model behavior
- Structuring complex interactions

### Key Difference: Resources vs Tools

The real difference is their **user interaction model**:
- **Tools**: Model-controlled - the LLM can discover and invoke tools automatically based on context
- **Resources**: Application-driven - the host application determines how to incorporate context

---

## Code Examples

### Complete Server with All Three Primitives

```python
from fastmcp import FastMCP
from fastmcp.context import Context

mcp = FastMCP("Demo MCP Server")

# ============ TOOLS ============

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers."""
    return a * b

@mcp.tool
async def fetch_user_data(user_id: int) -> dict:
    """Fetches user data from external API."""
    # Simulated async API call
    return {"user_id": user_id, "name": "John Doe", "active": True}

@mcp.tool
def add_numbers(x: int, y: int, ctx: Context) -> int:
    """Adds two numbers and logs the operation."""
    result = x + y
    ctx.info(f"Adding {x} + {y} = {result}")
    return result

# ============ RESOURCES ============

@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Returns a simple greeting message."""
    return "Hello from FastMCP Resources"

@mcp.resource("resource://config")
def get_config() -> dict:
    """Returns server configuration."""
    return {
        "version": "1.0.0",
        "environment": "production",
        "features": ["tools", "resources", "prompts"]
    }

@mcp.resource("resource://users/{user_id}")
def get_user_resource(user_id: str) -> dict:
    """Returns user resource by ID."""
    return {
        "user_id": user_id,
        "type": "resource",
        "timestamp": "2025-12-18"
    }

# ============ PROMPTS ============

@mcp.prompt
def explain_topic(topic: str) -> str:
    """Generates a query prompt for explanation of topic."""
    return f"Can you explain {topic} in a beginner friendly manner"

@mcp.prompt(
    name="custom_analysis",
    description="Analyzes data with specific focus",
    tags=["analysis", "data"]
)
def analyze_data(data_type: str, focus_area: str = "general") -> str:
    """Creates a prompt for data analysis."""
    return f"Analyze the {data_type} data with focus on {focus_area}"

# ============ CONTEXT USAGE ============

@mcp.tool
async def process_with_context(data: str, ctx: Context) -> str:
    """Demonstrates context usage for logging and progress."""
    ctx.info("Starting processing...")

    # Report progress
    ctx.report_progress(0.0, 1.0)

    # Simulate processing
    result = data.upper()

    ctx.report_progress(1.0, 1.0)
    ctx.info("Processing complete")

    return result

if __name__ == "__main__":
    mcp.run()
```

### Advanced Tool with Type Hints and Pydantic

```python
from pydantic import BaseModel, Field
from typing import Optional

class UserInput(BaseModel):
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    email: Optional[str] = Field(None, description="User's email")

@mcp.tool
def create_user(user: UserInput) -> dict:
    """Creates a new user with validated input."""
    return {
        "status": "created",
        "user": user.model_dump()
    }
```

### Resource Templates (Dynamic URLs)

```python
@mcp.resource("resource://documents/{doc_id}")
def get_document(doc_id: str) -> str:
    """Fetches a document by ID."""
    # In real implementation, fetch from database
    return f"Content of document {doc_id}"

@mcp.resource("resource://files/{category}/{filename}")
def get_file(category: str, filename: str) -> str:
    """Fetches a file from a specific category."""
    return f"File: {category}/{filename}"
```

---

## FastAPI Integration

FastMCP provides seamless integration with FastAPI applications through multiple patterns.

### Pattern 1: Auto-Generate MCP Server from FastAPI

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "John"}

@app.post("/users")
def create_user(name: str, email: str):
    return {"id": 1, "name": name, "email": email}

# Auto-generate MCP server from FastAPI app
mcp = FastMCP.from_fastapi(app=app)
```

### Pattern 2: Mount MCP Server to FastAPI

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()

# Create MCP server
mcp = FastMCP("Analytics MCP Server")

@mcp.tool
def analyze_data(metric: str) -> dict:
    return {"metric": metric, "value": 42}

# Create MCP HTTP app and mount it
mcp_app = mcp.http_app(path='/mcp')
app.mount("/analytics", mcp_app)

# Now you can run: uvicorn main:app
```

### Pattern 3: Route Mapping Configuration

```python
from fastmcp import FastMCP, RouteMap

app = FastAPI()

# Configure route mapping
route_map = RouteMap(
    get_to_resource=True,  # Map GET requests to Resources
    post_to_tool=True,     # Map POST requests to Tools
    put_to_tool=True,      # Map PUT requests to Tools
    delete_to_tool=True    # Map DELETE requests to Tools
)

mcp = FastMCP.from_fastapi(app=app, route_map=route_map)
```

### Pattern 4: Using fastapi-mcp Library

```python
from fastapi import FastAPI, Depends
from fastapi_mcp import FastApiMCP

app = FastAPI()

# Create FastApiMCP instance
mcp = FastApiMCP(
    app=app,
    name="My API",
    description="API with MCP support",
    base_url="http://localhost:8000"
)

# Mount MCP server
mcp.mount()

# MCP server available at /mcp
# All FastAPI routes automatically exposed as MCP tools
```

### Integration Best Practices

**For Bootstrapping/Prototyping:**
- Auto-generate from FastAPI is quick and easy
- Good for getting started quickly

**For Production:**
- Design dedicated MCP servers with curated tools
- LLMs achieve significantly better performance with well-designed MCP servers
- Don't just mirror your REST API to LLM clients

**Key Considerations:**
- FastMCP tightly couples your MCP server to your FastAPI app
- Route structure changes automatically update available MCP tools
- Good for smaller projects, but can create complexity as API evolves

---

## Testing MCP Servers

FastMCP 2.0 was designed to make rigorous testing easy through **in-memory testing patterns**.

### Why In-Memory Testing?

**Benefits:**
- Eliminates network dependencies
- No subprocess overhead
- Deterministic testing
- Full protocol compliance
- Fast and reliable

**Avoid:** Many developers attempt to test MCP servers by spawning subprocess instances, leading to race conditions and connection failures.

### Basic Testing Pattern

```python
from fastmcp import FastMCP, Client

mcp = FastMCP("My MCP Server")

@mcp.tool
def add(x: int, y: int) -> int:
    """Adds two numbers."""
    return x + y

async def main():
    # Connect via in-memory transport
    async with Client(mcp) as client:
        # Call a tool
        result = await client.call_tool(
            name="add",
            arguments={"x": 5, "y": 3}
        )
        print(result.data)  # 8
```

### Pytest Integration

```python
import pytest
from my_project.main import mcp
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport

@pytest.fixture
async def mcp_client():
    """Provides an MCP client for testing."""
    async with Client(mcp) as client:
        yield client

@pytest.mark.asyncio
async def test_add_tool(mcp_client: Client[FastMCPTransport]):
    """Test the add tool."""
    result = await mcp_client.call_tool(
        name="add",
        arguments={"x": 10, "y": 20}
    )
    assert result.data == 30

@pytest.mark.asyncio
async def test_greet_tool(mcp_client: Client[FastMCPTransport]):
    """Test the greet tool."""
    result = await mcp_client.call_tool(
        name="greet",
        arguments={"name": "Alice"}
    )
    assert result.data == "Hello, Alice!"
```

### Parameterized Tests

```python
@pytest.mark.parametrize(
    "first_number, second_number, expected",
    [(1, 2, 3), (2, 3, 5), (3, 4, 7), (10, -5, 5)],
)
async def test_add_parameterized(
    first_number: int,
    second_number: int,
    expected: int,
    mcp_client: Client[FastMCPTransport],
):
    """Test add tool with multiple input combinations."""
    result = await mcp_client.call_tool(
        name="add",
        arguments={"x": first_number, "y": second_number}
    )
    assert result.data == expected
```

### Testing Resources

```python
@pytest.mark.asyncio
async def test_config_resource(mcp_client: Client[FastMCPTransport]):
    """Test reading a resource."""
    resource = await mcp_client.read_resource("resource://config")
    assert "version" in resource.data
    assert resource.data["environment"] == "production"
```

### Testing with Mocks (External APIs)

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch('my_project.external_api.fetch_data')
async def test_tool_with_external_api(
    mock_fetch: AsyncMock,
    mcp_client: Client[FastMCPTransport]
):
    """Test tool that calls external API."""
    # Mock the external API response
    mock_fetch.return_value = {"status": "success", "data": [1, 2, 3]}

    result = await mcp_client.call_tool(
        name="process_external_data",
        arguments={"endpoint": "/api/data"}
    )

    assert result.data["status"] == "success"
    mock_fetch.assert_called_once()
```

### Testing Client Methods

Within an `async with client:` block, you can:

```python
async with Client(mcp) as client:
    # Ping the server
    await client.ping()

    # List available tools
    tools = await client.list_tools()

    # Call a tool
    result = await client.call_tool(name="add", arguments={"x": 1, "y": 2})

    # Read a resource
    resource = await client.read_resource("resource://config")

    # List resources
    resources = await client.list_resources()

    # Get prompts
    prompts = await client.list_prompts()
```

### Recommended Tools

- **inline-snapshot**: For asserting complex data structures
  ```python
  from inline_snapshot import snapshot

  assert result.data == snapshot({"expected": "structure"})
  ```

### Additional Testing Resources

The FastMCP repository contains thousands of tests covering:
- Remote MCP server connections
- Tools, resources, and prompts testing
- Authentication flows
- Error handling
- Edge cases

---

## Deployment Considerations

### Production Requirements

For an MCP server to be production-ready, it needs:

1. **Reliability**
   - Robust error handling
   - Graceful failure recovery
   - Automatic retry mechanisms

2. **Security**
   - Proper authentication and authorization
   - Data protection
   - Restricted access to authorized clients

3. **Scalability**
   - Handle increasing load
   - Horizontal scaling capability
   - Resource management

4. **Observability**
   - Logging and monitoring
   - Performance metrics
   - Health checks

5. **Operational Excellence**
   - Streamlined deployment
   - Easy updates and maintenance
   - Configuration management

### Transport Selection

**Stdio Transport**
- Traditional MCP connection method
- Good for local integrations
- Used by Claude Desktop and similar clients

**HTTP/SSE Transport (Recommended for Production)**
- Efficient and modern
- Runs as persistent HTTP server using Uvicorn
- Handles multiple client connections
- Compatible with reverse proxies (Nginx)
- Works with process managers (Supervisor, PM2)

```python
# Production HTTP server
mcp.run(
    transport="http",
    host="0.0.0.0",  # Listen on all interfaces
    port=int(os.getenv("PORT", "8000")),
    path="/mcp"
)
```

### Docker Deployment

**Basic Dockerfile Example**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose Example**

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Configuration Management

**Environment-Based Configuration**

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "MCP Server"
    environment: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"
    log_level: str = "info"
    database_url: str
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()

mcp = FastMCP(settings.app_name)

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port
    )
```

### API Gateway Integration

For microservice architectures, consider adding an API Gateway to:

- **Route Requests**: Expose MCP server externally via HTTPS
- **Authentication**: Implement JWT, OAuth2, or API keys
- **Rate Limiting**: Prevent abuse with throttling
- **Load Balancing**: Distribute traffic across multiple instances

### Monitoring and Logging

```python
import logging
from fastmcp import FastMCP
from fastmcp.context import Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("Production MCP Server")

@mcp.tool
def process_data(data: str, ctx: Context) -> dict:
    """Processes data with logging."""
    logger.info(f"Processing data: {data[:50]}...")
    ctx.info("Starting data processing")

    try:
        # Process data
        result = {"status": "success", "length": len(data)}
        logger.info(f"Processing complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        ctx.error(f"Error: {str(e)}")
        raise
```

### Security Best Practices

1. **Environment Variables**: Never hardcode secrets
2. **Authentication**: Use FastMCP's enterprise auth features
3. **HTTPS Only**: In production, always use HTTPS
4. **Input Validation**: Use Pydantic for strict type checking
5. **Rate Limiting**: Implement rate limits on tools
6. **Audit Logging**: Log all tool invocations

### Performance Optimization

- Use async functions for I/O-bound operations
- Implement caching for frequently accessed resources
- Connection pooling for database operations
- Optimize resource templates for dynamic data

---

## Relevance to Scheduling Domain

FastMCP is highly relevant to our scheduling application domain. Here's how it can enhance the Autonomous Assignment Program Manager:

### 1. Schedule Data Exposure (Resources)

**Expose Scheduling Data as Resources:**

```python
@mcp.resource("resource://schedules/employee/{employee_id}")
async def get_employee_schedule(employee_id: str) -> dict:
    """Returns the current schedule for an employee."""
    # Query database for employee schedule
    schedule = await db.get_employee_schedule(employee_id)
    return {
        "employee_id": employee_id,
        "shifts": schedule.shifts,
        "total_hours": schedule.total_hours,
        "period": schedule.period
    }

@mcp.resource("resource://schedules/coverage/{date}")
async def get_coverage_status(date: str) -> dict:
    """Returns coverage status for a specific date."""
    coverage = await db.get_coverage_for_date(date)
    return {
        "date": date,
        "required_staff": coverage.required,
        "assigned_staff": coverage.assigned,
        "status": coverage.status,
        "gaps": coverage.gaps
    }

@mcp.resource("resource://availability/{employee_id}")
async def get_employee_availability(employee_id: str) -> dict:
    """Returns employee availability and constraints."""
    availability = await db.get_availability(employee_id)
    return {
        "employee_id": employee_id,
        "available_shifts": availability.shifts,
        "time_off_requests": availability.time_off,
        "constraints": availability.constraints
    }
```

### 2. Scheduling Operations (Tools)

**Expose Scheduling Functions as Tools:**

```python
@mcp.tool
async def create_shift_assignment(
    employee_id: str,
    shift_date: str,
    shift_type: str,
    ctx: Context
) -> dict:
    """Assigns an employee to a shift."""
    ctx.info(f"Assigning {employee_id} to {shift_type} shift on {date}")

    # Validate assignment
    validation = await validate_assignment(employee_id, shift_date, shift_type)
    if not validation.is_valid:
        ctx.error(f"Assignment validation failed: {validation.reason}")
        raise ValueError(validation.reason)

    # Create assignment
    assignment = await db.create_shift_assignment(
        employee_id, shift_date, shift_type
    )

    ctx.info("Assignment created successfully")
    return {
        "assignment_id": assignment.id,
        "status": "confirmed",
        "details": assignment.to_dict()
    }

@mcp.tool
async def request_time_off(
    employee_id: str,
    start_date: str,
    end_date: str,
    absence_type: str,
    reason: str = None
) -> dict:
    """Submits a time-off request."""
    request = await db.create_absence_request(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        absence_type=absence_type,
        reason=reason,
        status="pending"
    )

    return {
        "request_id": request.id,
        "status": "pending",
        "requires_approval": True
    }

@mcp.tool
async def auto_schedule_period(
    start_date: str,
    end_date: str,
    department: str,
    ctx: Context
) -> dict:
    """Auto-generates schedule for a period using AI scheduling."""
    ctx.info(f"Auto-scheduling {department} from {start_date} to {end_date}")
    ctx.report_progress(0.0, 1.0)

    # Run scheduling algorithm
    schedule = await scheduler.generate_schedule(
        start_date, end_date, department
    )

    ctx.report_progress(0.5, 1.0)

    # Validate schedule
    validation = await scheduler.validate_schedule(schedule)

    ctx.report_progress(1.0, 1.0)
    ctx.info(f"Schedule generated with {len(schedule.assignments)} assignments")

    return {
        "schedule_id": schedule.id,
        "assignments_count": len(schedule.assignments),
        "coverage_percentage": validation.coverage_percentage,
        "constraint_violations": validation.violations
    }

@mcp.tool
async def check_schedule_conflicts(employee_id: str, date_range: str) -> dict:
    """Checks for scheduling conflicts for an employee."""
    conflicts = await scheduler.find_conflicts(employee_id, date_range)
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": [c.to_dict() for c in conflicts]
    }
```

### 3. AI-Assisted Scheduling (Prompts)

**Define Scheduling Prompts:**

```python
@mcp.prompt
def schedule_optimization_prompt(
    department: str,
    period: str,
    constraints: str = "standard"
) -> str:
    """Generates a prompt for AI-assisted schedule optimization."""
    return f"""
    Optimize the schedule for {department} for {period}.

    Consider the following:
    - Employee availability and preferences
    - Required coverage levels
    - Labor regulations and constraints: {constraints}
    - Fairness in shift distribution
    - Cost optimization

    Analyze the current schedule and suggest improvements.
    """

@mcp.prompt
def coverage_analysis_prompt(date: str, department: str) -> str:
    """Generates a prompt for coverage gap analysis."""
    return f"""
    Analyze the coverage for {department} on {date}.

    Identify:
    - Any coverage gaps or shortages
    - Overstaffed periods
    - Recommendations for addressing gaps
    - Employees available to fill gaps
    """

@mcp.prompt
def employee_schedule_request(employee_id: str, request_type: str) -> str:
    """Generates a prompt for employee schedule requests."""
    return f"""
    Process a {request_type} request for employee {employee_id}.

    Review:
    - Current schedule and commitments
    - Team coverage impact
    - Policy compliance
    - Alternative solutions if request cannot be approved
    """
```

### 4. Integration with Existing FastAPI Application

**Seamless Integration:**

```python
from fastapi import FastAPI
from fastmcp import FastMCP
from app.api.v1.router import api_router

# Existing FastAPI app
app = FastAPI(title="Autonomous Assignment Program Manager")
app.include_router(api_router, prefix="/api/v1")

# Create dedicated MCP server (recommended approach)
mcp = FastMCP("Scheduling MCP Server")

# Add scheduling-specific tools and resources
@mcp.resource("resource://schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    # Implementation
    pass

@mcp.tool
async def optimize_schedule(period: str, department: str):
    # Implementation
    pass

# Mount MCP server to FastAPI
mcp_app = mcp.http_app(path='/mcp')
app.mount("/mcp", mcp_app)

# Both REST API and MCP available:
# - REST API: http://localhost:8000/api/v1/...
# - MCP: http://localhost:8000/mcp
```

### 5. Use Cases for LLM Integration

**Natural Language Scheduling:**
- "Schedule John for morning shifts next week"
- "Find available staff to cover Friday night"
- "Show me all scheduling conflicts for December"

**Intelligent Analysis:**
- "Analyze overtime patterns this month"
- "Suggest schedule optimizations to reduce costs"
- "Identify fairness issues in shift distribution"

**Automated Workflows:**
- Auto-approve time-off requests based on policy
- Suggest replacements when employees call in sick
- Generate optimized schedules with AI assistance

### 6. Benefits for Our Project

1. **AI-Powered Scheduling**: LLMs can assist with complex scheduling decisions
2. **Natural Language Interface**: Users can interact with the system conversationally
3. **Automated Insights**: AI can analyze schedules and provide recommendations
4. **Enhanced Accessibility**: Non-technical users can perform complex operations
5. **Integration Ready**: Works alongside existing REST API
6. **Future-Proof**: Standardized protocol for AI integration

### 7. Example Integration Workflow

```python
# User interacts with Claude or other LLM:
# "Show me tomorrow's schedule and identify any coverage gaps"

# LLM uses MCP to:
# 1. Read resource: resource://schedules/coverage/2025-12-19
# 2. Call tool: check_coverage_gaps(date="2025-12-19")
# 3. Use prompt: coverage_analysis_prompt to structure response
# 4. Return natural language answer with actionable insights
```

---

## Conclusion

FastMCP provides a powerful, production-ready framework for exposing our scheduling application to LLM-powered interfaces. By implementing MCP servers alongside our existing FastAPI application, we can:

- Enable AI-assisted scheduling decisions
- Provide natural language access to scheduling data
- Automate complex scheduling workflows
- Improve user experience with conversational interfaces
- Maintain security and reliability in production

The framework's focus on simplicity, testability, and production-readiness makes it an excellent choice for enhancing the Autonomous Assignment Program Manager with modern AI capabilities.

---

## Sources

- [FastMCP Official Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [FastMCP Quickstart Guide](https://gofastmcp.com/getting-started/quickstart)
- [FastMCP Testing Documentation](https://gofastmcp.com/patterns/testing)
- [FastMCP FastAPI Integration](https://gofastmcp.com/integrations/fastapi)
- [DataCamp: Building MCP Server with FastMCP 2.0](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp)
- [FreeCodeCamp: How to Build Your First MCP Server](https://www.freecodecamp.org/news/how-to-build-your-first-mcp-server-using-fastmcp/)
- [Firecrawl: Complete FastMCP Tutorial for AI Developers](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python)
- [Composio: Using Prompts, Resources, and Tools in MCP](https://composio.dev/blog/how-to-effectively-use-prompts-resources-and-tools-in-mcp)
- [Building Production-Ready MCP Servers](https://thinhdanggroup.github.io/mcp-production-ready/)
- [Docker: Build to Production MCP Servers](https://www.docker.com/blog/build-to-prod-mcp-servers-with-docker/)
- [Speakeasy: Building FastAPI MCP Server](https://www.speakeasy.com/mcp/framework-guides/building-fastapi-server)
- [Implementing MCP in FastAPI Application](https://uselessai.in/implementing-mcp-architecture-in-a-fastapi-application-f513989b65d9)
- [MCPcat: Unit Testing MCP Servers Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/)
- [Introducing FastMCP 2.0](https://www.jlowin.dev/blog/fastmcp-2)
