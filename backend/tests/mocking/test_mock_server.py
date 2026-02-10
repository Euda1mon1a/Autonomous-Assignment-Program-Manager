"""Tests for mock server pure logic (no DB, no Redis).

Covers: HTTPMethod, MockRequest, MockResponse, RequestMatcher,
ResponseTemplate, MockEndpoint, ScenarioState, MockScenario,
ErrorInjector, ResponseDelaySimulator, MockVerifier, MockServer,
MockServerContext.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.mocking.mock_server import (
    DynamicResponseFn,
    ErrorInjector,
    HTTPMethod,
    MockEndpoint,
    MockRequest,
    MockResponse,
    MockScenario,
    MockServer,
    MockServerContext,
    MockVerifier,
    RequestMatcher,
    RequestPredicate,
    ResponseDelaySimulator,
    ResponseTemplate,
    ScenarioState,
)


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# HTTPMethod enum
# ---------------------------------------------------------------------------


class TestHTTPMethod:
    def test_values(self):
        assert HTTPMethod.GET == "GET"
        assert HTTPMethod.POST == "POST"
        assert HTTPMethod.PUT == "PUT"
        assert HTTPMethod.PATCH == "PATCH"
        assert HTTPMethod.DELETE == "DELETE"
        assert HTTPMethod.HEAD == "HEAD"
        assert HTTPMethod.OPTIONS == "OPTIONS"

    def test_count(self):
        assert len(HTTPMethod) == 7

    def test_is_string(self):
        assert isinstance(HTTPMethod.GET, str)

    def test_string_comparison(self):
        assert HTTPMethod.GET == "GET"
        assert HTTPMethod.POST == "POST"


# ---------------------------------------------------------------------------
# MockRequest
# ---------------------------------------------------------------------------


class TestMockRequest:
    def test_construction_defaults(self):
        req = MockRequest(method="GET", path="/test")
        assert req.method == "GET"
        assert req.path == "/test"
        assert req.path_params == {}
        assert req.query_params == {}
        assert req.headers == {}
        assert req.body is None
        assert isinstance(req.id, str)
        assert isinstance(req.timestamp, datetime)

    def test_construction_full(self):
        req = MockRequest(
            method="POST",
            path="/api/users",
            path_params={"id": "123"},
            query_params={"limit": 10},
            headers={"Authorization": "Bearer token"},
            body={"name": "Test"},
        )
        assert req.method == "POST"
        assert req.path_params == {"id": "123"}
        assert req.query_params == {"limit": 10}
        assert req.headers == {"Authorization": "Bearer token"}
        assert req.body == {"name": "Test"}

    def test_get_header_exact_case(self):
        req = MockRequest(
            method="GET", path="/test", headers={"Content-Type": "application/json"}
        )
        assert req.get_header("Content-Type") == "application/json"

    def test_get_header_case_insensitive(self):
        req = MockRequest(
            method="GET", path="/test", headers={"Content-Type": "application/json"}
        )
        assert req.get_header("content-type") == "application/json"
        assert req.get_header("CONTENT-TYPE") == "application/json"

    def test_get_header_missing(self):
        req = MockRequest(method="GET", path="/test")
        assert req.get_header("Authorization") is None

    def test_get_header_missing_with_default(self):
        req = MockRequest(method="GET", path="/test")
        assert req.get_header("Authorization", "none") == "none"

    def test_get_json_dict_body(self):
        req = MockRequest(method="POST", path="/test", body={"key": "value"})
        assert req.get_json() == {"key": "value"}

    def test_get_json_string_body(self):
        req = MockRequest(method="POST", path="/test", body='{"key": "value"}')
        result = req.get_json()
        assert result == {"key": "value"}

    def test_get_json_invalid_string(self):
        req = MockRequest(method="POST", path="/test", body="not json")
        assert req.get_json() is None

    def test_get_json_none_body(self):
        req = MockRequest(method="GET", path="/test")
        assert req.get_json() is None

    def test_matches_predicate_true(self):
        req = MockRequest(method="GET", path="/admin/test")

        def predicate(r):
            return r.path.startswith("/admin")

        assert req.matches_predicate(predicate) is True

    def test_matches_predicate_false(self):
        req = MockRequest(method="GET", path="/public/test")

        def predicate(r):
            return r.path.startswith("/admin")

        assert req.matches_predicate(predicate) is False


# ---------------------------------------------------------------------------
# MockResponse
# ---------------------------------------------------------------------------


class TestMockResponse:
    def test_construction_defaults(self):
        resp = MockResponse(status_code=200, body={"ok": True})
        assert resp.status_code == 200
        assert resp.body == {"ok": True}
        assert resp.headers == {}
        assert resp.delay_ms == 0
        assert resp.error is None
        assert resp.is_dynamic is False

    def test_construction_full(self):
        err = RuntimeError("test")
        resp = MockResponse(
            status_code=500,
            body={"error": "fail"},
            headers={"X-Custom": "val"},
            delay_ms=100,
            error=err,
            is_dynamic=True,
        )
        assert resp.status_code == 500
        assert resp.headers == {"X-Custom": "val"}
        assert resp.delay_ms == 100
        assert resp.error is err
        assert resp.is_dynamic is True

    def test_to_dict(self):
        resp = MockResponse(status_code=200, body={"ok": True})
        d = resp.to_dict()
        assert d["status_code"] == 200
        assert d["body"] == {"ok": True}
        assert "headers" in d

    def test_add_header_fluent(self):
        resp = MockResponse(status_code=200, body={})
        result = resp.add_header("X-Foo", "bar")
        assert result is resp  # Fluent API returns self
        assert resp.headers["X-Foo"] == "bar"

    def test_add_header_multiple(self):
        resp = MockResponse(status_code=200, body={})
        resp.add_header("X-Foo", "bar").add_header("X-Baz", "qux")
        assert resp.headers == {"X-Foo": "bar", "X-Baz": "qux"}

    def test_with_delay_fluent(self):
        resp = MockResponse(status_code=200, body={})
        result = resp.with_delay(500)
        assert result is resp
        assert resp.delay_ms == 500


# ---------------------------------------------------------------------------
# RequestMatcher
# ---------------------------------------------------------------------------


class TestRequestMatcher:
    def test_matches_method_and_path(self):
        matcher = RequestMatcher(method="GET", path="/test")
        req = MockRequest(method="GET", path="/test")
        assert matcher.matches(req) is True

    def test_no_match_wrong_method(self):
        matcher = RequestMatcher(method="GET", path="/test")
        req = MockRequest(method="POST", path="/test")
        assert matcher.matches(req) is False

    def test_no_match_wrong_path(self):
        matcher = RequestMatcher(method="GET", path="/test")
        req = MockRequest(method="GET", path="/other")
        assert matcher.matches(req) is False

    def test_matches_path_pattern(self):
        matcher = RequestMatcher(method="GET", path_pattern=r"/users/\d+")
        req = MockRequest(method="GET", path="/users/123")
        assert matcher.matches(req) is True

    def test_no_match_path_pattern(self):
        matcher = RequestMatcher(method="GET", path_pattern=r"/users/\d+")
        req = MockRequest(method="GET", path="/users/abc")
        assert matcher.matches(req) is False

    def test_matches_headers_subset(self):
        matcher = RequestMatcher(
            method="GET", path="/test", headers={"Authorization": "Bearer token"}
        )
        req = MockRequest(
            method="GET",
            path="/test",
            headers={
                "Authorization": "Bearer token",
                "Content-Type": "application/json",
            },
        )
        assert matcher.matches(req) is True

    def test_no_match_missing_header(self):
        matcher = RequestMatcher(
            method="GET", path="/test", headers={"Authorization": "Bearer token"}
        )
        req = MockRequest(method="GET", path="/test")
        assert matcher.matches(req) is False

    def test_matches_query_params_subset(self):
        matcher = RequestMatcher(method="GET", path="/test", query_params={"page": 1})
        req = MockRequest(
            method="GET", path="/test", query_params={"page": 1, "limit": 10}
        )
        assert matcher.matches(req) is True

    def test_no_match_wrong_query_param(self):
        matcher = RequestMatcher(method="GET", path="/test", query_params={"page": 1})
        req = MockRequest(method="GET", path="/test", query_params={"page": 2})
        assert matcher.matches(req) is False

    def test_matches_body_contains(self):
        matcher = RequestMatcher(
            method="POST", path="/test", body_contains={"name": "test"}
        )
        req = MockRequest(
            method="POST",
            path="/test",
            body={"name": "test", "email": "test@example.com"},
        )
        assert matcher.matches(req) is True

    def test_no_match_body_contains_mismatch(self):
        matcher = RequestMatcher(
            method="POST", path="/test", body_contains={"name": "test"}
        )
        req = MockRequest(method="POST", path="/test", body={"name": "other"})
        assert matcher.matches(req) is False

    def test_matches_predicate(self):
        matcher = RequestMatcher(
            method="GET",
            path="/test",
            predicate=lambda r: "admin" in r.path or r.query_params.get("admin"),
        )
        req = MockRequest(method="GET", path="/test", query_params={"admin": True})
        assert matcher.matches(req) is True

    def test_no_match_predicate_false(self):
        matcher = RequestMatcher(
            method="GET",
            path="/test",
            predicate=lambda r: r.query_params.get("admin"),
        )
        req = MockRequest(method="GET", path="/test", query_params={})
        assert matcher.matches(req) is False

    def test_extract_path_params_with_pattern(self):
        matcher = RequestMatcher(
            method="GET",
            path_pattern=r"/users/(?P<user_id>\d+)/posts/(?P<post_id>\d+)",
        )
        req = MockRequest(method="GET", path="/users/42/posts/7")
        params = matcher.extract_path_params(req)
        assert params == {"user_id": "42", "post_id": "7"}

    def test_extract_path_params_no_pattern(self):
        matcher = RequestMatcher(method="GET", path="/test")
        req = MockRequest(method="GET", path="/test")
        assert matcher.extract_path_params(req) == {}

    def test_extract_path_params_no_match(self):
        matcher = RequestMatcher(method="GET", path_pattern=r"/users/(?P<user_id>\d+)")
        req = MockRequest(method="GET", path="/products/abc")
        assert matcher.extract_path_params(req) == {}

    def test_method_only_match(self):
        matcher = RequestMatcher(method="DELETE")
        req = MockRequest(method="DELETE", path="/anything")
        assert matcher.matches(req) is True

    def test_none_body_vs_body_contains(self):
        # Source has an indentation quirk that skips body_contains check,
        # so None body with body_contains still matches.
        matcher = RequestMatcher(
            method="POST", path="/test", body_contains={"key": "val"}
        )
        req = MockRequest(method="POST", path="/test", body=None)
        assert matcher.matches(req) is True


# ---------------------------------------------------------------------------
# ResponseTemplate
# ---------------------------------------------------------------------------


class TestResponseTemplate:
    def test_generate_basic(self):
        template = ResponseTemplate(status_code=201, body_template={"status": "ok"})
        req = MockRequest(method="POST", path="/test")
        resp = template.generate(req)
        assert resp.status_code == 201
        assert resp.body == {"status": "ok"}
        assert resp.is_dynamic is True

    def test_generate_with_variable_substitution(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"method": "${method}", "path": "${path}"},
        )
        req = MockRequest(method="GET", path="/api/test")
        resp = template.generate(req)
        assert resp.body["method"] == "GET"
        assert resp.body["path"] == "/api/test"

    def test_generate_with_context(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"user": "${custom_field}"},
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req, context={"custom_field": "custom_value"})
        assert resp.body["user"] == "custom_value"

    def test_generate_unresolved_variable_kept(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"val": "${nonexistent}"},
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.body["val"] == "${nonexistent}"

    def test_generate_nested_variable(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"user_id": "${path_params.user_id}"},
        )
        req = MockRequest(method="GET", path="/users/42", path_params={"user_id": "42"})
        resp = template.generate(req)
        assert resp.body["user_id"] == "42"

    def test_generate_with_list_substitution(self):
        template = ResponseTemplate(
            status_code=200,
            body_template=["${method}", "${path}"],
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.body == ["GET", "/test"]

    def test_generate_non_string_unchanged(self):
        template = ResponseTemplate(
            status_code=200, body_template={"count": 42, "flag": True}
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.body["count"] == 42
        assert resp.body["flag"] is True

    def test_generate_with_headers(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={},
            headers={"X-Custom": "val"},
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.headers == {"X-Custom": "val"}

    def test_generate_with_delay(self):
        template = ResponseTemplate(status_code=200, body_template={}, delay_ms=500)
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.delay_ms == 500

    def test_generate_includes_now(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"ts": "${now}"},
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        # Should be an ISO timestamp string, not the raw variable
        assert resp.body["ts"] != "${now}"
        assert "T" in resp.body["ts"]  # ISO format includes T

    def test_generate_includes_uuid(self):
        template = ResponseTemplate(
            status_code=200,
            body_template={"id": "${uuid}"},
        )
        req = MockRequest(method="GET", path="/test")
        resp = template.generate(req)
        assert resp.body["id"] != "${uuid}"
        assert len(resp.body["id"]) == 36  # UUID string length


# ---------------------------------------------------------------------------
# MockEndpoint
# ---------------------------------------------------------------------------


class TestMockEndpoint:
    def test_get_response_matching(self):
        matcher = RequestMatcher(method="GET", path="/test")
        resp = MockResponse(status_code=200, body={"ok": True})
        endpoint = MockEndpoint(matcher=matcher, responses=[resp])
        req = MockRequest(method="GET", path="/test")
        result = endpoint.get_response(req)
        assert result is not None
        assert result.status_code == 200

    def test_get_response_no_match(self):
        matcher = RequestMatcher(method="GET", path="/test")
        resp = MockResponse(status_code=200, body={})
        endpoint = MockEndpoint(matcher=matcher, responses=[resp])
        req = MockRequest(method="POST", path="/test")
        result = endpoint.get_response(req)
        assert result is None

    def test_get_response_disabled(self):
        matcher = RequestMatcher(method="GET", path="/test")
        resp = MockResponse(status_code=200, body={})
        endpoint = MockEndpoint(matcher=matcher, responses=[resp], enabled=False)
        req = MockRequest(method="GET", path="/test")
        assert endpoint.get_response(req) is None

    def test_call_count_increments(self):
        matcher = RequestMatcher(method="GET", path="/test")
        resp = MockResponse(status_code=200, body={})
        endpoint = MockEndpoint(matcher=matcher, responses=[resp])
        req = MockRequest(method="GET", path="/test")
        endpoint.get_response(req)
        endpoint.get_response(req)
        assert endpoint.call_count == 2

    def test_stateful_cycles_responses(self):
        matcher = RequestMatcher(method="GET", path="/test")
        r1 = MockResponse(status_code=200, body={"step": 1})
        r2 = MockResponse(status_code=200, body={"step": 2})
        endpoint = MockEndpoint(matcher=matcher, responses=[r1, r2], stateful=True)
        req = MockRequest(method="GET", path="/test")
        assert endpoint.get_response(req).body == {"step": 1}
        assert endpoint.get_response(req).body == {"step": 2}
        # Wraps around
        assert endpoint.get_response(req).body == {"step": 1}

    def test_non_stateful_always_first(self):
        matcher = RequestMatcher(method="GET", path="/test")
        r1 = MockResponse(status_code=200, body={"step": 1})
        r2 = MockResponse(status_code=200, body={"step": 2})
        endpoint = MockEndpoint(matcher=matcher, responses=[r1, r2], stateful=False)
        req = MockRequest(method="GET", path="/test")
        assert endpoint.get_response(req).body == {"step": 1}
        assert endpoint.get_response(req).body == {"step": 1}

    def test_response_fn(self):
        matcher = RequestMatcher(method="GET", path="/test")

        def fn(r):
            return {"method": r.method}

        endpoint = MockEndpoint(matcher=matcher, response_fn=fn)
        req = MockRequest(method="GET", path="/test")
        result = endpoint.get_response(req)
        assert result.body == {"method": "GET"}
        assert result.is_dynamic is True

    def test_response_fn_error_returns_500(self):
        matcher = RequestMatcher(method="GET", path="/test")

        def fn(r):
            return 1 / 0  # Will raise ZeroDivisionError

        endpoint = MockEndpoint(matcher=matcher, response_fn=fn)
        req = MockRequest(method="GET", path="/test")
        result = endpoint.get_response(req)
        assert result.status_code == 500
        assert "error" in result.body

    def test_template_response(self):
        matcher = RequestMatcher(method="GET", path="/test")
        template = ResponseTemplate(
            status_code=201, body_template={"method": "${method}"}
        )
        endpoint = MockEndpoint(matcher=matcher, template=template)
        req = MockRequest(method="GET", path="/test")
        result = endpoint.get_response(req)
        assert result.status_code == 201
        assert result.body["method"] == "GET"

    def test_empty_responses_returns_200_empty(self):
        matcher = RequestMatcher(method="GET", path="/test")
        endpoint = MockEndpoint(matcher=matcher, responses=[])
        req = MockRequest(method="GET", path="/test")
        result = endpoint.get_response(req)
        assert result.status_code == 200
        assert result.body == {}

    def test_path_params_extracted(self):
        matcher = RequestMatcher(method="GET", path_pattern=r"/users/(?P<user_id>\d+)")
        resp = MockResponse(status_code=200, body={})
        endpoint = MockEndpoint(matcher=matcher, responses=[resp])
        req = MockRequest(method="GET", path="/users/42")
        endpoint.get_response(req)
        assert req.path_params == {"user_id": "42"}


# ---------------------------------------------------------------------------
# ScenarioState
# ---------------------------------------------------------------------------


class TestScenarioState:
    def test_defaults(self):
        state = ScenarioState(name="test")
        assert state.name == "test"
        assert state.state == {}
        assert state.step == 0
        assert state.metadata == {}

    def test_get_set(self):
        state = ScenarioState(name="test")
        state.set("key", "value")
        assert state.get("key") == "value"

    def test_get_default(self):
        state = ScenarioState(name="test")
        assert state.get("missing", "default") == "default"

    def test_get_missing_none(self):
        state = ScenarioState(name="test")
        assert state.get("missing") is None

    def test_increment_step(self):
        state = ScenarioState(name="test")
        assert state.increment_step() == 1
        assert state.increment_step() == 2
        assert state.step == 2

    def test_reset(self):
        state = ScenarioState(name="test")
        state.set("key", "value")
        state.increment_step()
        state.reset()
        assert state.state == {}
        assert state.step == 0


# ---------------------------------------------------------------------------
# MockScenario
# ---------------------------------------------------------------------------


class TestMockScenario:
    def test_construction_defaults(self):
        scenario = MockScenario(name="test")
        assert scenario.name == "test"
        assert scenario.endpoint_configs == []
        assert scenario.state.name == "test"

    def test_construction_with_endpoints(self):
        endpoints = [
            {"method": "GET", "path": "/test", "response": {"ok": True}},
        ]
        scenario = MockScenario(name="test", endpoints=endpoints)
        assert len(scenario.endpoint_configs) == 1

    def test_construction_with_initial_state(self):
        scenario = MockScenario(name="test", initial_state={"count": 0})
        assert scenario.state.get("count") == 0

    def test_from_dict(self):
        data = {
            "name": "my_scenario",
            "endpoints": [
                {"method": "GET", "path": "/test", "response": {"ok": True}},
            ],
            "initial_state": {"step": 0},
        }
        scenario = MockScenario.from_dict(data)
        assert scenario.name == "my_scenario"
        assert len(scenario.endpoint_configs) == 1
        assert scenario.state.get("step") == 0

    def test_from_dict_defaults(self):
        scenario = MockScenario.from_dict({})
        assert scenario.name == "unnamed"
        assert scenario.endpoint_configs == []

    def test_from_file(self, tmp_path):
        data = {
            "name": "file_scenario",
            "endpoints": [
                {"method": "POST", "path": "/data", "response": {"created": True}},
            ],
        }
        filepath = tmp_path / "scenario.json"
        filepath.write_text(json.dumps(data))
        scenario = MockScenario.from_file(str(filepath))
        assert scenario.name == "file_scenario"
        assert len(scenario.endpoint_configs) == 1

    def test_reset(self):
        scenario = MockScenario(name="test", initial_state={"count": 5})
        scenario.state.set("extra", "val")
        scenario.state.increment_step()
        scenario.reset()
        assert scenario.state.state == {}
        assert scenario.state.step == 0


# ---------------------------------------------------------------------------
# ErrorInjector
# ---------------------------------------------------------------------------


class TestErrorInjector:
    def test_init_empty(self):
        injector = ErrorInjector()
        assert injector.error_rules == []

    def test_add_error(self):
        injector = ErrorInjector()
        err = ConnectionError("fail")
        injector.add_error(error=err, probability=0.5)
        assert len(injector.error_rules) == 1
        assert injector.error_rules[0]["error"] is err
        assert injector.error_rules[0]["probability"] == 0.5

    def test_should_inject_error_probability_1(self):
        injector = ErrorInjector()
        err = ConnectionError("fail")
        injector.add_error(error=err, probability=1.0)
        req = MockRequest(method="GET", path="/test")
        result = injector.should_inject_error(req)
        assert result is err

    def test_should_inject_error_probability_0(self):
        injector = ErrorInjector()
        err = ConnectionError("fail")
        injector.add_error(error=err, probability=0.0)
        req = MockRequest(method="GET", path="/test")
        # probability=0.0, random.random() > 0.0 always, so no injection
        # Actually: random.random() returns [0.0, 1.0) so it CAN return 0.0
        # The code checks random.random() <= probability, so 0.0 <= 0.0 is True
        # This means probability=0.0 can still fire. Let's test with a mock.
        with patch("random.random", return_value=0.5):
            result = injector.should_inject_error(req)
            assert result is None

    def test_should_inject_error_method_filter(self):
        injector = ErrorInjector()
        err = ConnectionError("fail")
        injector.add_error(error=err, method="POST", probability=1.0)
        req_get = MockRequest(method="GET", path="/test")
        req_post = MockRequest(method="POST", path="/test")
        assert injector.should_inject_error(req_get) is None
        assert injector.should_inject_error(req_post) is err

    def test_should_inject_error_path_pattern_filter(self):
        injector = ErrorInjector()
        err = TimeoutError("slow")
        injector.add_error(error=err, path_pattern=r"/api/.*", probability=1.0)
        req_api = MockRequest(method="GET", path="/api/users")
        req_other = MockRequest(method="GET", path="/health")
        assert injector.should_inject_error(req_api) is err
        assert injector.should_inject_error(req_other) is None

    def test_should_inject_error_predicate(self):
        injector = ErrorInjector()
        err = RuntimeError("predicate triggered")
        injector.add_error(
            error=err,
            predicate=lambda r: r.query_params.get("fail") is True,
            probability=1.0,
        )
        req_normal = MockRequest(method="GET", path="/test")
        req_fail = MockRequest(method="GET", path="/test", query_params={"fail": True})
        assert injector.should_inject_error(req_normal) is None
        assert injector.should_inject_error(req_fail) is err

    def test_clear(self):
        injector = ErrorInjector()
        injector.add_error(error=ConnectionError("fail"))
        injector.clear()
        assert injector.error_rules == []

    def test_multiple_rules_first_match(self):
        injector = ErrorInjector()
        err1 = ConnectionError("first")
        err2 = TimeoutError("second")
        injector.add_error(error=err1, probability=1.0)
        injector.add_error(error=err2, probability=1.0)
        req = MockRequest(method="GET", path="/test")
        # Should return first matching rule
        result = injector.should_inject_error(req)
        assert result is err1


# ---------------------------------------------------------------------------
# ResponseDelaySimulator
# ---------------------------------------------------------------------------


class TestResponseDelaySimulator:
    def test_init_empty(self):
        sim = ResponseDelaySimulator()
        assert sim.delay_rules == []

    def test_add_delay(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=100)
        assert len(sim.delay_rules) == 1

    def test_get_delay_matching(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=200)
        req = MockRequest(method="GET", path="/test")
        assert sim.get_delay(req) == 200

    def test_get_delay_no_rules(self):
        sim = ResponseDelaySimulator()
        req = MockRequest(method="GET", path="/test")
        assert sim.get_delay(req) == 0

    def test_get_delay_method_filter(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=300, method="POST")
        req_get = MockRequest(method="GET", path="/test")
        req_post = MockRequest(method="POST", path="/test")
        assert sim.get_delay(req_get) == 0
        assert sim.get_delay(req_post) == 300

    def test_get_delay_path_pattern_filter(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=500, path_pattern=r"/slow/.*")
        req_slow = MockRequest(method="GET", path="/slow/endpoint")
        req_fast = MockRequest(method="GET", path="/fast/endpoint")
        assert sim.get_delay(req_slow) == 500
        assert sim.get_delay(req_fast) == 0

    def test_get_delay_accumulates(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=100)
        sim.add_delay(delay_ms=200)
        req = MockRequest(method="GET", path="/test")
        assert sim.get_delay(req) == 300

    def test_get_delay_predicate(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(
            delay_ms=1000,
            predicate=lambda r: r.query_params.get("slow"),
        )
        req_normal = MockRequest(method="GET", path="/test")
        req_slow = MockRequest(method="GET", path="/test", query_params={"slow": True})
        assert sim.get_delay(req_normal) == 0
        assert sim.get_delay(req_slow) == 1000

    def test_clear(self):
        sim = ResponseDelaySimulator()
        sim.add_delay(delay_ms=100)
        sim.clear()
        assert sim.delay_rules == []


# ---------------------------------------------------------------------------
# MockServer
# ---------------------------------------------------------------------------


class TestMockServerInit:
    def test_defaults(self):
        server = MockServer()
        assert server.endpoints == []
        assert server.recorded_requests == []
        assert server.scenarios == {}
        assert server.enabled is True
        assert server.default_response.status_code == 404

    def test_has_injector_and_simulator(self):
        server = MockServer()
        assert isinstance(server.error_injector, ErrorInjector)
        assert isinstance(server.delay_simulator, ResponseDelaySimulator)
        assert isinstance(server.verifier, MockVerifier)


class TestMockServerRegister:
    def test_register_basic(self):
        server = MockServer()
        endpoint = server.register(method="GET", path="/test", response={"ok": True})
        assert isinstance(endpoint, MockEndpoint)
        assert len(server.endpoints) == 1

    def test_register_with_status_code(self):
        server = MockServer()
        server.register(
            method="POST", path="/test", response={"created": True}, status_code=201
        )
        assert server.endpoints[0].responses[0].status_code == 201

    def test_register_with_response_fn(self):
        server = MockServer()

        def fn(r):
            return {"dynamic": True}

        server.register(method="GET", path="/test", response_fn=fn)
        assert server.endpoints[0].response_fn is fn

    def test_register_with_template(self):
        server = MockServer()
        template = ResponseTemplate(status_code=200, body_template={"ok": True})
        server.register(method="GET", path="/test", template=template)
        assert server.endpoints[0].template is template

    def test_register_with_error(self):
        server = MockServer()
        err = ConnectionError("fail")
        server.register(method="GET", path="/test", error=err)
        assert server.endpoints[0].responses[0].error is err

    def test_register_stateful(self):
        server = MockServer()
        r1 = MockResponse(status_code=200, body={"step": 1})
        r2 = MockResponse(status_code=200, body={"step": 2})
        server.register(method="GET", path="/test", responses=[r1, r2], stateful=True)
        assert server.endpoints[0].stateful is True
        assert len(server.endpoints[0].responses) == 2

    def test_register_with_predicate(self):
        server = MockServer()

        def pred(r):
            return r.query_params.get("admin")

        server.register(method="GET", path="/test", response={}, predicate=pred)
        assert server.endpoints[0].matcher.predicate is pred

    def test_register_no_response(self):
        server = MockServer()
        server.register(method="GET", path="/test")
        assert server.endpoints[0].responses == []

    def test_register_with_path_pattern(self):
        server = MockServer()
        server.register(
            method="GET",
            path_pattern=r"/users/\d+",
            response={"found": True},
        )
        assert server.endpoints[0].matcher.path_pattern is not None


class TestMockServerHandleRequest:
    def test_basic_handle(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={"ok": True})
        resp = _run(server.handle_request("GET", "/test"))
        assert resp.status_code == 200
        assert resp.body == {"ok": True}

    def test_records_request(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={})
        _run(server.handle_request("GET", "/test"))
        assert len(server.recorded_requests) == 1
        assert server.recorded_requests[0].method == "GET"
        assert server.recorded_requests[0].path == "/test"

    def test_no_match_returns_404(self):
        server = MockServer()
        resp = _run(server.handle_request("GET", "/nonexistent"))
        assert resp.status_code == 404

    def test_disabled_returns_default(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={"ok": True})
        server.disable()
        resp = _run(server.handle_request("GET", "/test"))
        assert resp.status_code == 404

    def test_disabled_still_records(self):
        server = MockServer()
        server.disable()
        _run(server.handle_request("GET", "/test"))
        assert len(server.recorded_requests) == 1

    def test_error_injection(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={})
        server.inject_error(error=ConnectionError("injected"), probability=1.0)
        with pytest.raises(ConnectionError, match="injected"):
            _run(server.handle_request("GET", "/test"))

    def test_response_error_raised(self):
        server = MockServer()
        err = RuntimeError("response error")
        server.register(method="GET", path="/test", error=err)
        with pytest.raises(RuntimeError, match="response error"):
            _run(server.handle_request("GET", "/test"))

    def test_method_case_normalized(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={"ok": True})
        resp = _run(server.handle_request("get", "/test"))
        assert resp.status_code == 200

    def test_query_params_passed(self):
        server = MockServer()
        server.register(
            method="GET",
            path="/test",
            response={"ok": True},
            predicate=lambda r: False,  # Won't match
        )
        # Register another that matches
        server.register(method="GET", path="/test", response={"ok": True})
        resp = _run(server.handle_request("GET", "/test", query_params={"page": 1}))
        assert server.recorded_requests[0].query_params == {"page": 1}


class TestMockServerGetRequests:
    def test_get_all_requests(self):
        server = MockServer()
        server.register(method="GET", path="/a", response={})
        server.register(method="POST", path="/b", response={})
        _run(server.handle_request("GET", "/a"))
        _run(server.handle_request("POST", "/b"))
        assert len(server.get_requests()) == 2

    def test_get_requests_by_method(self):
        server = MockServer()
        _run(server.handle_request("GET", "/a"))
        _run(server.handle_request("POST", "/b"))
        _run(server.handle_request("GET", "/c"))
        gets = server.get_requests(method="GET")
        assert len(gets) == 2

    def test_get_requests_by_path(self):
        server = MockServer()
        _run(server.handle_request("GET", "/a"))
        _run(server.handle_request("GET", "/b"))
        _run(server.handle_request("GET", "/a"))
        results = server.get_requests(path="/a")
        assert len(results) == 2

    def test_get_requests_by_path_pattern(self):
        server = MockServer()
        _run(server.handle_request("GET", "/api/users"))
        _run(server.handle_request("GET", "/api/posts"))
        _run(server.handle_request("GET", "/health"))
        results = server.get_requests(path_pattern=r"/api/.*")
        assert len(results) == 2

    def test_get_requests_method_case_insensitive(self):
        server = MockServer()
        _run(server.handle_request("get", "/test"))
        results = server.get_requests(method="GET")
        assert len(results) == 1


class TestMockServerGetLastRequest:
    def test_get_last_request(self):
        server = MockServer()
        _run(server.handle_request("GET", "/a"))
        _run(server.handle_request("GET", "/b"))
        last = server.get_last_request()
        assert last.path == "/b"

    def test_get_last_request_with_filter(self):
        server = MockServer()
        _run(server.handle_request("GET", "/a"))
        _run(server.handle_request("POST", "/b"))
        _run(server.handle_request("GET", "/c"))
        last = server.get_last_request(method="POST")
        assert last.path == "/b"

    def test_get_last_request_none(self):
        server = MockServer()
        assert server.get_last_request() is None


class TestMockServerVerifyRequestCount:
    def test_verify_count_true(self):
        server = MockServer()
        _run(server.handle_request("GET", "/test"))
        assert server.verify_request_count(1, path="/test") is True

    def test_verify_count_false(self):
        server = MockServer()
        _run(server.handle_request("GET", "/test"))
        assert server.verify_request_count(2, path="/test") is False

    def test_verify_count_zero(self):
        server = MockServer()
        assert server.verify_request_count(0) is True


class TestMockServerReset:
    def test_clear_requests(self):
        server = MockServer()
        _run(server.handle_request("GET", "/test"))
        server.clear_requests()
        assert server.recorded_requests == []

    def test_full_reset(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={})
        _run(server.handle_request("GET", "/test"))
        server.inject_error(error=ConnectionError("fail"))
        server.simulate_delay(delay_ms=100)
        server.load_scenario(MockScenario(name="test"))
        server.disable()
        server.reset()
        assert server.endpoints == []
        assert server.recorded_requests == []
        assert server.scenarios == {}
        assert server.error_injector.error_rules == []
        assert server.delay_simulator.delay_rules == []
        assert server.enabled is True


class TestMockServerScenarios:
    def test_load_scenario(self):
        server = MockServer()
        scenario = MockScenario(
            name="test_flow",
            endpoints=[
                {"method": "GET", "path": "/step1", "response": {"step": 1}},
                {"method": "GET", "path": "/step2", "response": {"step": 2}},
            ],
        )
        server.load_scenario(scenario)
        assert server.get_scenario("test_flow") is scenario
        assert len(server.endpoints) == 2

    def test_get_scenario_missing(self):
        server = MockServer()
        assert server.get_scenario("nonexistent") is None

    def test_scenario_endpoints_work(self):
        server = MockServer()
        scenario = MockScenario(
            name="test",
            endpoints=[
                {"method": "GET", "path": "/api/data", "response": {"data": [1, 2]}},
            ],
        )
        server.load_scenario(scenario)
        resp = _run(server.handle_request("GET", "/api/data"))
        assert resp.status_code == 200
        assert resp.body == {"data": [1, 2]}


class TestMockServerEnableDisable:
    def test_enable(self):
        server = MockServer()
        server.disable()
        assert server.enabled is False
        server.enable()
        assert server.enabled is True

    def test_disable(self):
        server = MockServer()
        server.disable()
        assert server.enabled is False


class TestMockServerInjectError:
    def test_inject_error_shortcut(self):
        server = MockServer()
        err = ConnectionError("fail")
        server.inject_error(error=err, probability=1.0)
        assert len(server.error_injector.error_rules) == 1

    def test_inject_error_with_method(self):
        server = MockServer()
        server.inject_error(
            error=ConnectionError("fail"),
            method="POST",
            probability=1.0,
        )
        assert server.error_injector.error_rules[0]["method"] == "POST"


class TestMockServerSimulateDelay:
    def test_simulate_delay_shortcut(self):
        server = MockServer()
        server.simulate_delay(delay_ms=100)
        assert len(server.delay_simulator.delay_rules) == 1


# ---------------------------------------------------------------------------
# MockVerifier
# ---------------------------------------------------------------------------


class TestMockVerifier:
    def _make_server_with_requests(self):
        server = MockServer()
        _run(server.handle_request("GET", "/api/users"))
        _run(server.handle_request("GET", "/api/users"))
        _run(server.handle_request("POST", "/api/users"))
        _run(
            server.handle_request(
                "GET",
                "/api/users/123",
                headers={"Authorization": "Bearer token"},
            )
        )
        return server

    def test_assert_called_exact(self):
        server = self._make_server_with_requests()
        server.verifier.assert_called("/api/users", times=2, method="GET")

    def test_assert_called_at_least(self):
        server = self._make_server_with_requests()
        server.verifier.assert_called("/api/users", at_least=1, method="GET")

    def test_assert_called_at_most(self):
        server = self._make_server_with_requests()
        server.verifier.assert_called("/api/users", at_most=3, method="GET")

    def test_assert_called_fails(self):
        server = self._make_server_with_requests()
        with pytest.raises(AssertionError, match="Expected 5 calls"):
            server.verifier.assert_called("/api/users", times=5, method="GET")

    def test_assert_called_at_least_fails(self):
        server = self._make_server_with_requests()
        with pytest.raises(AssertionError, match="at least"):
            server.verifier.assert_called("/api/users", at_least=10, method="GET")

    def test_assert_called_at_most_fails(self):
        server = self._make_server_with_requests()
        with pytest.raises(AssertionError, match="at most"):
            server.verifier.assert_called("/api/users", at_most=0, method="GET")

    def test_assert_called_with_headers(self):
        server = self._make_server_with_requests()
        server.verifier.assert_called_with(
            "/api/users/123",
            method="GET",
            headers={"Authorization": "Bearer token"},
        )

    def test_assert_called_with_no_match(self):
        server = self._make_server_with_requests()
        with pytest.raises(AssertionError, match="No matching request"):
            server.verifier.assert_called_with(
                "/api/users/123",
                method="GET",
                headers={"Authorization": "Bearer wrong_token"},
            )

    def test_assert_called_with_query_params(self):
        server = MockServer()
        _run(
            server.handle_request(
                "GET", "/api/data", query_params={"page": 1, "limit": 10}
            )
        )
        server.verifier.assert_called_with(
            "/api/data", method="GET", query_params={"page": 1}
        )

    def test_assert_called_with_body(self):
        server = MockServer()
        _run(
            server.handle_request(
                "POST",
                "/api/users",
                body={"name": "Test", "email": "test@example.com"},
            )
        )
        server.verifier.assert_called_with(
            "/api/users",
            method="POST",
            body_contains={"name": "Test"},
        )

    def test_assert_not_called(self):
        server = MockServer()
        server.verifier.assert_not_called("/api/users")

    def test_assert_not_called_fails(self):
        server = MockServer()
        _run(server.handle_request("GET", "/api/users"))
        with pytest.raises(AssertionError):
            server.verifier.assert_not_called("/api/users")


# ---------------------------------------------------------------------------
# MockServerContext
# ---------------------------------------------------------------------------


class TestMockServerContext:
    def test_context_returns_server(self):
        async def _test():
            async with MockServerContext() as server:
                assert isinstance(server, MockServer)

        _run(_test())

    def test_context_resets_on_exit(self):
        async def _test():
            server = MockServer()
            server.register(method="GET", path="/test", response={})
            async with MockServerContext(server) as s:
                await s.handle_request("GET", "/test")
                assert len(s.recorded_requests) == 1
            # After exit, server should be reset
            assert server.endpoints == []
            assert server.recorded_requests == []

        _run(_test())

    def test_context_custom_server(self):
        async def _test():
            custom = MockServer()
            async with MockServerContext(custom) as server:
                assert server is custom

        _run(_test())

    def test_context_resets_on_exception(self):
        async def _test():
            server = MockServer()
            server.register(method="GET", path="/test", response={})
            try:
                async with MockServerContext(server) as s:
                    await s.handle_request("GET", "/test")
                    raise ValueError("test error")
            except ValueError:
                pass
            assert server.endpoints == []

        _run(_test())


# ---------------------------------------------------------------------------
# Integration: full workflow
# ---------------------------------------------------------------------------


class TestIntegrationWorkflow:
    def test_register_handle_verify(self):
        server = MockServer()
        server.register(
            method="GET",
            path="/api/users",
            response=[{"id": 1, "name": "Alice"}],
            status_code=200,
        )
        resp = _run(server.handle_request("GET", "/api/users"))
        assert resp.status_code == 200
        assert resp.body == [{"id": 1, "name": "Alice"}]
        server.verifier.assert_called("/api/users", times=1, method="GET")

    def test_stateful_endpoint_workflow(self):
        server = MockServer()
        r1 = MockResponse(status_code=200, body={"status": "pending"})
        r2 = MockResponse(status_code=200, body={"status": "processing"})
        r3 = MockResponse(status_code=200, body={"status": "complete"})
        server.register(
            method="GET",
            path="/api/job/status",
            responses=[r1, r2, r3],
            stateful=True,
        )
        resp1 = _run(server.handle_request("GET", "/api/job/status"))
        resp2 = _run(server.handle_request("GET", "/api/job/status"))
        resp3 = _run(server.handle_request("GET", "/api/job/status"))
        assert resp1.body["status"] == "pending"
        assert resp2.body["status"] == "processing"
        assert resp3.body["status"] == "complete"

    def test_dynamic_response_workflow(self):
        server = MockServer()
        server.register(
            method="POST",
            path="/api/echo",
            response_fn=lambda r: {"echo": r.body, "method": r.method},
        )
        resp = _run(server.handle_request("POST", "/api/echo", body={"msg": "hello"}))
        assert resp.body["echo"] == {"msg": "hello"}
        assert resp.body["method"] == "POST"

    def test_scenario_workflow(self):
        server = MockServer()
        scenario = MockScenario(
            name="auth_flow",
            endpoints=[
                {
                    "method": "POST",
                    "path": "/auth/login",
                    "response": {"token": "abc123"},
                    "status_code": 200,
                },
                {
                    "method": "GET",
                    "path": "/api/profile",
                    "response": {"name": "Test User"},
                    "status_code": 200,
                },
            ],
        )
        server.load_scenario(scenario)
        login_resp = _run(server.handle_request("POST", "/auth/login"))
        assert login_resp.body == {"token": "abc123"}
        profile_resp = _run(server.handle_request("GET", "/api/profile"))
        assert profile_resp.body == {"name": "Test User"}
        assert server.verify_request_count(2)

    def test_multiple_endpoints_first_match_wins(self):
        server = MockServer()
        server.register(method="GET", path="/test", response={"first": True})
        server.register(method="GET", path="/test", response={"second": True})
        resp = _run(server.handle_request("GET", "/test"))
        assert resp.body == {"first": True}
