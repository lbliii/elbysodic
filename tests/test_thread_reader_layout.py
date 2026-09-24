from __future__ import annotations

import asyncio

from chirp.testing import TestClient

from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app


def _remove_first_author_poster(services: AppServices) -> str:
    thread = services.read_thread("danger-room", "sentinel-drill")
    author = thread.posts[0].author
    services.repo.update_character(
        services.seed.community.id,
        author.id,
        slug=author.slug,
        name=author.name,
        avatar_url=author.avatar_url,
        poster_url=None,
        poster_alt="",
        tagline=author.tagline,
        accent_color=author.accent_color,
        summary=author.summary,
        post_profile_variant=author.post_profile_variant,
        post_accent_style=author.post_accent_style,
        post_border_style=author.post_border_style,
        post_title_style=author.post_title_style,
        post_density=author.post_density,
    )
    return author.name


def test_member_thread_reader_uses_one_path_and_compact_missing_art_context() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        first_author_name = _remove_first_author_poster(services)
        active_face = services.seed.default_character
        assert active_face is not None
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        assert page.status == 200
        assert page.text.count('class="elbysodic-place-toolbar__breadcrumbs"') == 1
        assert "chirpui-breadcrumbs" in page.text
        assert 'class="elbysodic-scene-reader-breadcrumbs elbysodic-visually-hidden"' in page.text
        assert 'aria-label="Scene breadcrumbs" aria-hidden="true" inert' in page.text
        assert 'aria-labelledby="scene-title"' in page.text
        assert page.text.index('id="scene-title"') < page.text.index('id="post-1"')
        assert 'class="elbysodic-post__poster-media elbysodic-character-poster--' in page.text
        assert f'<span aria-hidden="true">{first_author_name[:1]}</span>' in page.text
        assert "elbysodic-scene-context-drawer" in page.text
        assert f'<option value="{active_face.id}" selected>' in page.text

    asyncio.run(run())


def test_public_thread_preview_keeps_its_boundary_and_reading_order() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        first_author_name = _remove_first_author_poster(services)
        community = services.seed.community
        services.repo.update_community_launch_status(community.id, "public-preview")
        public_app = create_app(debug=False, services=AppServices(services.repo, None))

        async with TestClient(public_app) as client:
            page = await client.get(
                f"/c/{community.slug}/boards/danger-room/threads/sentinel-drill"
            )

        assert page.status == 200
        assert "Public scene preview" in page.text
        assert 'aria-labelledby="public-preview-posts"' in page.text
        assert page.text.index('aria-labelledby="public-preview-posts"') < page.text.index(
            'id="post-1"'
        )
        assert f"<span>{first_author_name[:1]}</span>" in page.text
        assert "Request access" in page.text
        assert "realm-only posts and participate with a face of your own" in page.text
        assert 'id="reply-composer"' not in page.text
        assert "Scene context" not in page.text

    asyncio.run(run())
