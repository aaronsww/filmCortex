"""Generate embeddings for movies that do not have one yet.

Run after ingestion jobs:
    uv run python -m pipeline.jobs.generate_embeddings
"""

import argparse
import asyncio
import logging

from filmcortex.config.settings import settings
from filmcortex.core.logging import configure_logging
from filmcortex.db.session import async_session_factory
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.services.movie_embedding import MovieEmbeddingService
from pipeline.shared.limits import resolve_limit

logger = logging.getLogger(__name__)


async def run(*, limit: int) -> None:
    configure_logging()

    async with async_session_factory() as session:
        service = MovieEmbeddingService(
            embedding_repository=MovieEmbeddingRepository(session),
        )
        stats = await service.generate_all(limit=limit)
        await session.commit()

    print(f"Pending {stats.pending} movies without embeddings")
    print(f"Generated {stats.generated}")
    print(f"Failed {stats.failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate movie embeddings")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of embeddings to generate "
            f"(default: {settings.embedding_batch_size} from EMBEDDING_BATCH_SIZE)"
        ),
    )
    args = parser.parse_args()
    asyncio.run(run(limit=resolve_limit(args.limit, settings.embedding_batch_size)))


if __name__ == "__main__":
    main()
