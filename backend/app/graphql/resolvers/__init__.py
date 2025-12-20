"""GraphQL resolvers."""

from app.graphql.resolvers.mutations import Mutation
from app.graphql.resolvers.queries import Query

__all__ = ["Query", "Mutation"]
