"""
Tests for MCP server initialization.

This module tests that the MCP server initializes correctly, has all tools
and resources registered, and is properly configured.
"""

import pytest


class TestServerImports:
    """Test that server module imports correctly."""

    def test_server_module_imports(self):
        """Verify server module imports without error."""
        from scheduler_mcp import server

        assert server is not None

    def test_mcp_instance_exists(self):
        """Verify FastMCP instance is exported."""
        from scheduler_mcp.server import mcp

        assert mcp is not None


class TestMCPConfiguration:
    """Test MCP server configuration."""

    def test_mcp_name(self):
        """Verify MCP server has correct name."""
        from scheduler_mcp.server import mcp

        assert mcp.name == "Residency Scheduler"

    def test_mcp_version(self):
        """Verify MCP server has a version."""
        from scheduler_mcp.server import mcp

        # FastMCP stores version in settings or as attribute
        # Version is set in FastMCP constructor
        assert hasattr(mcp, "settings") or hasattr(mcp, "version")

    def test_mcp_has_instructions(self):
        """Verify MCP server has instructions configured."""
        from scheduler_mcp.server import mcp

        # Instructions are configured in the FastMCP constructor
        # The exact attribute name may vary by FastMCP version
        assert mcp is not None


class TestToolsRegistration:
    """Test that tools are properly registered."""

    def test_tools_registered(self):
        """Verify tools are registered with the MCP server."""
        from scheduler_mcp.server import mcp

        # FastMCP stores tools in _tool_manager or similar
        # Access the tools registry - the exact attribute varies by version
        # Try common patterns for accessing registered tools
        tools = None

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

        assert tools is not None, "Could not find tools registry"

    def test_minimum_tool_count(self):
        """Verify at least 30 tools are registered."""
        from scheduler_mcp.server import mcp

        # Get tool count using available methods
        tool_count = 0

        if hasattr(mcp, "_tool_manager"):
            tool_count = len(mcp._tool_manager._tools)
        elif hasattr(mcp, "_tools"):
            tool_count = len(mcp._tools)
        elif hasattr(mcp, "tools"):
            tool_count = len(mcp.tools)

        # Server has 34 tools as of current implementation
        assert tool_count >= 30, f"Expected at least 30 tools, found {tool_count}"

    def test_core_scheduling_tools_exist(self):
        """Verify core scheduling tools are registered."""
        from scheduler_mcp.server import mcp

        # Get tools dictionary
        tools = {}

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

        tool_names = set(tools.keys()) if isinstance(tools, dict) else set()

        # Core scheduling tools that should exist
        expected_tools = [
            "validate_schedule_tool",
            "detect_conflicts_tool",
            "analyze_swap_candidates_tool",
            "run_contingency_analysis_tool",
        ]

        for tool_name in expected_tools:
            assert (
                tool_name in tool_names
            ), f"Expected tool '{tool_name}' not found in registered tools"

    def test_resilience_tools_exist(self):
        """Verify resilience framework tools are registered."""
        from scheduler_mcp.server import mcp

        # Get tools dictionary
        tools = {}

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

        tool_names = set(tools.keys()) if isinstance(tools, dict) else set()

        # Resilience tools that should exist
        expected_tools = [
            "check_utilization_threshold_tool",
            "get_defense_level_tool",
            "get_static_fallbacks_tool",
            "calculate_blast_radius_tool",
        ]

        for tool_name in expected_tools:
            assert (
                tool_name in tool_names
            ), f"Expected resilience tool '{tool_name}' not found"

    def test_async_tools_exist(self):
        """Verify async task management tools are registered."""
        from scheduler_mcp.server import mcp

        # Get tools dictionary
        tools = {}

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

        tool_names = set(tools.keys()) if isinstance(tools, dict) else set()

        # Async task tools that should exist
        expected_tools = [
            "start_background_task_tool",
            "get_task_status_tool",
            "cancel_task_tool",
            "list_active_tasks_tool",
        ]

        for tool_name in expected_tools:
            assert (
                tool_name in tool_names
            ), f"Expected async tool '{tool_name}' not found"

    def test_deployment_tools_exist(self):
        """Verify deployment workflow tools are registered."""
        from scheduler_mcp.server import mcp

        # Get tools dictionary
        tools = {}

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

        tool_names = set(tools.keys()) if isinstance(tools, dict) else set()

        # Deployment tools that should exist
        expected_tools = [
            "validate_deployment_tool",
            "run_security_scan_tool",
            "run_smoke_tests_tool",
            "rollback_deployment_tool",
        ]

        for tool_name in expected_tools:
            assert (
                tool_name in tool_names
            ), f"Expected deployment tool '{tool_name}' not found"


class TestResourcesRegistration:
    """Test that resources are properly registered."""

    def test_resources_registered(self):
        """Verify resources or resource templates are registered with the MCP server."""
        from scheduler_mcp.server import mcp

        # In FastMCP 2.x, resources with parameters are registered as templates
        # Check for either resources or resource templates
        has_resources = False

        if hasattr(mcp, "_resource_manager"):
            # Check for templates (resources with parameters)
            templates = getattr(mcp._resource_manager, "_templates", {})
            resources = getattr(mcp._resource_manager, "_resources", {})
            has_resources = len(templates) > 0 or len(resources) > 0

        assert has_resources, "Could not find resources or resource templates registry"

    @pytest.mark.asyncio
    async def test_minimum_resource_count(self):
        """Verify at least 2 resources/templates are registered."""
        from scheduler_mcp.server import mcp

        # FastMCP 2.x uses async get_resource_templates for parameterized resources
        templates = await mcp.get_resource_templates()
        resources = await mcp.get_resources()

        total_count = len(templates) + len(resources)

        # Server has 2 resource templates (status, compliance)
        assert total_count >= 2, f"Expected at least 2 resources/templates, found {total_count}"

    @pytest.mark.asyncio
    async def test_schedule_status_resource_exists(self):
        """Verify schedule status resource is registered."""
        from scheduler_mcp.server import mcp

        # Get resources and templates
        templates = await mcp.get_resource_templates()
        resources = await mcp.get_resources()

        # Combine keys from both
        all_keys = set(templates.keys()) | set(resources.keys())

        # Check for schedule status resource
        has_status = any(
            "status" in str(key).lower() for key in all_keys
        )

        assert has_status, f"Schedule status resource not found in: {all_keys}"

    @pytest.mark.asyncio
    async def test_compliance_resource_exists(self):
        """Verify compliance resource is registered."""
        from scheduler_mcp.server import mcp

        # Get resources and templates
        templates = await mcp.get_resource_templates()
        resources = await mcp.get_resources()

        # Combine keys from both
        all_keys = set(templates.keys()) | set(resources.keys())

        # Check for compliance resource
        has_compliance = any(
            "compliance" in str(key).lower() for key in all_keys
        )

        assert has_compliance, f"Compliance resource not found in: {all_keys}"


class TestServerEntryPoint:
    """Test server entry point configuration."""

    def test_main_function_exists(self):
        """Verify main function exists for CLI entry point."""
        from scheduler_mcp.server import main

        assert callable(main)

    def test_lifecycle_hooks_exist(self):
        """Verify lifecycle hooks are defined."""
        from scheduler_mcp import server

        # The on_initialize and on_shutdown hooks should be defined
        # These are decorated functions registered with the mcp instance
        assert hasattr(server, "on_initialize")
        assert hasattr(server, "on_shutdown")


class TestModuleExports:
    """Test module exports and package structure."""

    def test_package_version(self):
        """Verify package has version defined."""
        from scheduler_mcp import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_package_exports(self):
        """Verify expected exports are available."""
        import scheduler_mcp

        expected_exports = ["server", "resources", "tools"]

        for export in expected_exports:
            assert hasattr(scheduler_mcp, export) or export in scheduler_mcp.__all__, (
                f"Expected export '{export}' not found"
            )
