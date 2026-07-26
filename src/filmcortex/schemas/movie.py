import uuid

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class MovieListItem(BaseModel):
    id: uuid.UUID
    canonical_title: str
    provider: str
    provider_id: str


class MovieListPage(BaseModel):
    items: list[MovieListItem]
    next_cursor: str | None = None
    page_size: int = Field(ge=1, le=MAX_PAGE_SIZE)


class MovieStats(BaseModel):
    movies: int
    embeddings: int
    pending_embeddings: int


class SimilarMovie(MovieListItem):
    similarity_score: float | None = None
