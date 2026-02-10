"""Tests for Content Security Policy configuration (pure logic, no DB)."""

import pytest

from app.security.csp import ContentSecurityPolicy as CSP


# -- Constants ---------------------------------------------------------------


class TestDirectiveConstants:
    def test_default_src(self):
        assert CSP.DEFAULT_SRC == "default-src"

    def test_script_src(self):
        assert CSP.SCRIPT_SRC == "script-src"

    def test_style_src(self):
        assert CSP.STYLE_SRC == "style-src"

    def test_img_src(self):
        assert CSP.IMG_SRC == "img-src"

    def test_connect_src(self):
        assert CSP.CONNECT_SRC == "connect-src"

    def test_frame_src(self):
        assert CSP.FRAME_SRC == "frame-src"

    def test_object_src(self):
        assert CSP.OBJECT_SRC == "object-src"

    def test_frame_ancestors(self):
        assert CSP.FRAME_ANCESTORS == "frame-ancestors"

    def test_upgrade_insecure(self):
        assert CSP.UPGRADE_INSECURE_REQUESTS == "upgrade-insecure-requests"


class TestSourceConstants:
    def test_self(self):
        assert CSP.SELF == "'self'"

    def test_none(self):
        assert CSP.NONE == "'none'"

    def test_unsafe_inline(self):
        assert CSP.UNSAFE_INLINE == "'unsafe-inline'"

    def test_unsafe_eval_constant(self):
        # CSP UNSAFE_EVAL constant for development policy
        assert CSP.UNSAFE_EVAL == "'unsafe-eval'"  # @gorgon-ok CSP directive

    def test_data(self):
        assert CSP.DATA == "data:"

    def test_blob(self):
        assert CSP.BLOB == "blob:"

    def test_https(self):
        assert CSP.HTTPS == "https:"


# -- Production policy -------------------------------------------------------


class TestProductionPolicy:
    def test_returns_dict(self):
        policy = CSP.get_production_policy()
        assert isinstance(policy, dict)

    def test_default_src_self(self):
        policy = CSP.get_production_policy()
        assert policy[CSP.DEFAULT_SRC] == [CSP.SELF]

    def test_script_src_self_only(self):
        policy = CSP.get_production_policy()
        assert policy[CSP.SCRIPT_SRC] == [CSP.SELF]

    def test_no_unsafe_inline_in_production(self):
        policy = CSP.get_production_policy()
        for directive, sources in policy.items():
            assert CSP.UNSAFE_INLINE not in sources, (
                f"unsafe-inline found in {directive}"
            )

    def test_no_unsafe_eval_in_production(self):
        # Production must not allow code evaluation via CSP directives
        policy = CSP.get_production_policy()
        for directive, sources in policy.items():
            assert CSP.UNSAFE_EVAL not in sources, (
                f"CSP eval directive found in {directive}"
            )

    def test_object_src_none(self):
        policy = CSP.get_production_policy()
        assert policy[CSP.OBJECT_SRC] == [CSP.NONE]

    def test_frame_ancestors_none(self):
        policy = CSP.get_production_policy()
        assert policy[CSP.FRAME_ANCESTORS] == [CSP.NONE]

    def test_frame_src_none(self):
        policy = CSP.get_production_policy()
        assert policy[CSP.FRAME_SRC] == [CSP.NONE]

    def test_upgrade_insecure_requests(self):
        policy = CSP.get_production_policy()
        assert CSP.UPGRADE_INSECURE_REQUESTS in policy
        assert policy[CSP.UPGRADE_INSECURE_REQUESTS] == []

    def test_img_allows_data_and_https(self):
        policy = CSP.get_production_policy()
        assert CSP.DATA in policy[CSP.IMG_SRC]
        assert CSP.HTTPS in policy[CSP.IMG_SRC]

    def test_worker_allows_blob(self):
        policy = CSP.get_production_policy()
        assert CSP.BLOB in policy[CSP.WORKER_SRC]


# -- Development policy ------------------------------------------------------


class TestDevelopmentPolicy:
    def test_returns_dict(self):
        policy = CSP.get_development_policy()
        assert isinstance(policy, dict)

    def test_script_allows_unsafe_inline(self):
        policy = CSP.get_development_policy()
        assert CSP.UNSAFE_INLINE in policy[CSP.SCRIPT_SRC]

    def test_script_allows_csp_eval_directive(self):
        # Dev policy permits code evaluation CSP directive for HMR
        policy = CSP.get_development_policy()
        assert CSP.UNSAFE_EVAL in policy[CSP.SCRIPT_SRC]  # @gorgon-ok CSP directive

    def test_script_allows_localhost(self):
        policy = CSP.get_development_policy()
        assert any("localhost" in s for s in policy[CSP.SCRIPT_SRC])

    def test_style_allows_unsafe_inline(self):
        policy = CSP.get_development_policy()
        assert CSP.UNSAFE_INLINE in policy[CSP.STYLE_SRC]

    def test_connect_allows_ws_localhost(self):
        policy = CSP.get_development_policy()
        assert any("ws://" in s for s in policy[CSP.CONNECT_SRC])

    def test_object_src_still_none(self):
        policy = CSP.get_development_policy()
        assert policy[CSP.OBJECT_SRC] == [CSP.NONE]

    def test_frame_ancestors_still_none(self):
        policy = CSP.get_development_policy()
        assert policy[CSP.FRAME_ANCESTORS] == [CSP.NONE]

    def test_no_upgrade_insecure(self):
        policy = CSP.get_development_policy()
        assert CSP.UPGRADE_INSECURE_REQUESTS not in policy


# -- API policy --------------------------------------------------------------


class TestApiPolicy:
    def test_returns_dict(self):
        policy = CSP.get_api_policy()
        assert isinstance(policy, dict)

    def test_default_src_none(self):
        policy = CSP.get_api_policy()
        assert policy[CSP.DEFAULT_SRC] == [CSP.NONE]

    def test_script_src_none(self):
        policy = CSP.get_api_policy()
        assert policy[CSP.SCRIPT_SRC] == [CSP.NONE]

    def test_style_src_none(self):
        policy = CSP.get_api_policy()
        assert policy[CSP.STYLE_SRC] == [CSP.NONE]

    def test_connect_src_self(self):
        policy = CSP.get_api_policy()
        assert policy[CSP.CONNECT_SRC] == [CSP.SELF]

    def test_most_directives_none(self):
        policy = CSP.get_api_policy()
        none_directives = [
            CSP.DEFAULT_SRC,
            CSP.SCRIPT_SRC,
            CSP.STYLE_SRC,
            CSP.IMG_SRC,
            CSP.FONT_SRC,
            CSP.FRAME_SRC,
            CSP.OBJECT_SRC,
            CSP.MEDIA_SRC,
            CSP.WORKER_SRC,
            CSP.FORM_ACTION,
            CSP.FRAME_ANCESTORS,
            CSP.BASE_URI,
        ]
        for d in none_directives:
            assert policy[d] == [CSP.NONE], f"{d} should be 'none'"


# -- build_header_value ------------------------------------------------------


class TestBuildHeaderValue:
    def test_single_directive(self):
        policy = {"default-src": ["'self'"]}
        result = CSP.build_header_value(policy)
        assert result == "default-src 'self'"

    def test_multiple_sources(self):
        policy = {"script-src": ["'self'", "'unsafe-inline'"]}
        result = CSP.build_header_value(policy)
        assert result == "script-src 'self' 'unsafe-inline'"

    def test_multiple_directives(self):
        policy = {"default-src": ["'self'"], "script-src": ["'none'"]}
        result = CSP.build_header_value(policy)
        assert "default-src 'self'" in result
        assert "script-src 'none'" in result
        assert "; " in result

    def test_empty_sources_directive_only(self):
        policy = {"upgrade-insecure-requests": []}
        result = CSP.build_header_value(policy)
        assert result == "upgrade-insecure-requests"

    def test_empty_policy(self):
        result = CSP.build_header_value({})
        assert result == ""

    def test_production_header_format(self):
        policy = CSP.get_production_policy()
        result = CSP.build_header_value(policy)
        assert "default-src 'self'" in result
        assert "object-src 'none'" in result
        assert "upgrade-insecure-requests" in result


# -- get_header --------------------------------------------------------------


class TestGetHeader:
    def test_production_header_name(self):
        name, _ = CSP.get_header()
        assert name == "Content-Security-Policy"

    def test_development_header_name(self):
        name, _ = CSP.get_header(debug=True)
        assert name == "Content-Security-Policy"

    def test_api_header_name(self):
        name, _ = CSP.get_header(api_only=True)
        assert name == "Content-Security-Policy"

    def test_production_no_unsafe_inline(self):
        _, value = CSP.get_header()
        assert "'unsafe-inline'" not in value

    def test_production_no_unsafe_eval_directive(self):
        # Production CSP header must not contain code evaluation directives
        _, value = CSP.get_header()
        assert CSP.UNSAFE_EVAL not in value  # @gorgon-ok CSP directive check

    def test_development_has_unsafe_inline(self):
        _, value = CSP.get_header(debug=True)
        assert "'unsafe-inline'" in value

    def test_development_has_eval_directive(self):
        # Dev CSP header contains code evaluation directive for HMR
        _, value = CSP.get_header(debug=True)
        assert CSP.UNSAFE_EVAL in value  # @gorgon-ok CSP directive check

    def test_api_very_restrictive(self):
        _, value = CSP.get_header(api_only=True)
        assert "default-src 'none'" in value

    def test_api_overrides_debug(self):
        _, value = CSP.get_header(debug=True, api_only=True)
        assert "default-src 'none'" in value

    def test_returns_tuple(self):
        result = CSP.get_header()
        assert isinstance(result, tuple)
        assert len(result) == 2


# -- get_report_only_header --------------------------------------------------


class TestGetReportOnlyHeader:
    def test_report_only_name(self):
        name, _ = CSP.get_report_only_header()
        assert name == "Content-Security-Policy-Report-Only"

    def test_report_only_production(self):
        name, value = CSP.get_report_only_header(debug=False)
        assert name == "Content-Security-Policy-Report-Only"
        assert "'unsafe-inline'" not in value

    def test_report_only_development(self):
        name, value = CSP.get_report_only_header(debug=True)
        assert name == "Content-Security-Policy-Report-Only"
        assert "'unsafe-inline'" in value


# -- add_source / remove_source ----------------------------------------------


class TestAddSource:
    def test_add_to_existing(self):
        policy = {"script-src": ["'self'"]}
        CSP.add_source(policy, "script-src", "https://cdn.example.com")
        assert "https://cdn.example.com" in policy["script-src"]

    def test_add_to_new_directive(self):
        policy = {}
        CSP.add_source(policy, "img-src", "'self'")
        assert policy["img-src"] == ["'self'"]

    def test_no_duplicate(self):
        policy = {"script-src": ["'self'"]}
        CSP.add_source(policy, "script-src", "'self'")
        assert policy["script-src"].count("'self'") == 1

    def test_add_multiple(self):
        policy = {"script-src": ["'self'"]}
        CSP.add_source(policy, "script-src", "https://a.com")
        CSP.add_source(policy, "script-src", "https://b.com")
        assert len(policy["script-src"]) == 3


class TestRemoveSource:
    def test_remove_existing(self):
        policy = {"script-src": ["'self'", "'unsafe-inline'"]}
        CSP.remove_source(policy, "script-src", "'unsafe-inline'")
        assert "'unsafe-inline'" not in policy["script-src"]
        assert "'self'" in policy["script-src"]

    def test_remove_nonexistent_source(self):
        policy = {"script-src": ["'self'"]}
        CSP.remove_source(policy, "script-src", "'unsafe-inline'")
        assert policy["script-src"] == ["'self'"]

    def test_remove_from_nonexistent_directive(self):
        policy = {}
        CSP.remove_source(policy, "script-src", "'self'")
        assert policy == {}

    def test_remove_last_source(self):
        policy = {"script-src": ["'self'"]}
        CSP.remove_source(policy, "script-src", "'self'")
        assert policy["script-src"] == []
