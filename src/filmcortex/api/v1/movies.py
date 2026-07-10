import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from filmcortex.api.deps import get_movie_query_service, get_movie_similarity_service
from filmcortex.schemas.movie import MovieListItem, SimilarMovie
from filmcortex.services.movie_query import MovieQueryService
from filmcortex.services.movie_similarity import MovieSimilarityService

router = APIRouter()


@router.get("/movies", response_model=list[MovieListItem])
async def list_movies(
    movie_query_service: MovieQueryService = Depends(get_movie_query_service),
) -> list[MovieListItem]:
    return await movie_query_service.list_movies()


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
