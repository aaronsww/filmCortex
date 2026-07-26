import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from filmcortex.api.deps import get_movie_query_service, get_movie_similarity_service
from filmcortex.schemas.movie import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MovieListPage,
    MovieStats,
    SimilarMovie,
)
from filmcortex.services.movie_query import MovieQueryService
from filmcortex.services.movie_similarity import MovieSimilarityService
from filmcortex.utils.cursor import CursorError

router = APIRouter()


@router.get("/movies", response_model=MovieListPage)
async def list_movies(
    cursor: str | None = Query(default=None),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    movie_query_service: MovieQueryService = Depends(get_movie_query_service),
) -> MovieListPage:
    try:
        return await movie_query_service.list_movies(cursor=cursor, page_size=page_size)
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/movies/stats", response_model=MovieStats)
async def movie_stats(
    movie_query_service: MovieQueryService = Depends(get_movie_query_service),
) -> MovieStats:
    return await movie_query_service.get_stats()


@router.get(
    "/movies/{movie_id}/similar",
    response_model=list[SimilarMovie],
    response_model_exclude_none=True,
)
async def list_similar_movies(
    movie_id: uuid.UUID,
    include_scores: bool = Query(default=False),
    movie_similarity_service: MovieSimilarityService = Depends(get_movie_similarity_service),
) -> list[SimilarMovie]:
    similar = await movie_similarity_service.find_similar(
        movie_id,
        include_scores=include_scores,
    )
    if similar is None:
        raise HTTPException(status_code=404, detail="Movie not found or has no embedding")
    return similar
