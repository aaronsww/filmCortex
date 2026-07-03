from fastapi import APIRouter, Depends

from filmcortex.api.deps import get_movie_query_service
from filmcortex.schemas.movie import MovieListItem
from filmcortex.services.movie_query import MovieQueryService

router = APIRouter()


@router.get("/movies", response_model=list[MovieListItem])
async def list_movies(
    movie_query_service: MovieQueryService = Depends(get_movie_query_service),
) -> list[MovieListItem]:
    return await movie_query_service.list_movies()
