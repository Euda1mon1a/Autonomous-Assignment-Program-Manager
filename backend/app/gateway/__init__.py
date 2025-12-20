"""
API Gateway Package.

Provides API gateway patterns including:
- Dynamic routing
- Response aggregation
- Request/response transformation
- Service proxy
- Load balancing
- Service discovery integration
"""
from app.gateway.aggregator import ResponseAggregator, AggregationStrategy
from app.gateway.proxy import ServiceProxy, ProxyConfig
from app.gateway.router import DynamicRouter, RouteRule, RouteConfig
from app.gateway.transformer import (
    RequestTransformer,
    ResponseTransformer,
    TransformationPipeline,
)

__all__ = [
    "ResponseAggregator",
    "AggregationStrategy",
    "ServiceProxy",
    "ProxyConfig",
    "DynamicRouter",
    "RouteRule",
    "RouteConfig",
    "RequestTransformer",
    "ResponseTransformer",
    "TransformationPipeline",
]
