import uuid

from pydantic import BaseModel


class MovieListItem(BaseModel):
    id: uuid.UUID
    canonical_title: str
    provider: str
    provider_id: str


class SimilarMovie(MovieListItem):
    similarity_score: float | None = None
