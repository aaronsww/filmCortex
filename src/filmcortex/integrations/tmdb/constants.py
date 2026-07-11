TMDB_PROVIDER = "tmdb"
TMDB_PAYLOAD_VERSION = "2"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_EXPORT_BASE_URL = "https://files.tmdb.org/p/exports"

# Combined in a single movie details request via append_to_response.
TMDB_APPEND_TO_RESPONSE = (
    "credits,keywords,external_ids,images,videos,alternative_titles,translations"
)

# Discover sweeps for weekly/monthly notable-film coverage.
DISCOVER_SWEEPS: list[dict[str, str | int | float]] = [
    {
        "primary_release_year": 2024,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 500,
    },
    {
        "primary_release_year": 2023,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 500,
    },
    {
        "primary_release_year": 2020,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "primary_release_year": 2010,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "primary_release_year": 2000,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "primary_release_year": 1990,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "primary_release_year": 1980,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 500,
    },
    {
        "primary_release_year": 1970,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 500,
    },
    {
        "with_genres": 18,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "with_genres": 28,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
    {
        "with_genres": 878,
        "sort_by": "vote_average.desc",
        "vote_count.gte": 1000,
    },
]
