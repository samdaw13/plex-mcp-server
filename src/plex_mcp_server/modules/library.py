import asyncio
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession
from mcp.types import ToolAnnotations
from plexapi.exceptions import NotFound
from plexapi.server import PlexServer

from ..types.enums import ToolTag
from ..types.models import (
    ErrorResponse,
    LibraryContentsResponse,
    LibraryDetailsResponse,
    LibraryInfo,
    LibraryListResponse,
    LibraryRecentlyAddedResponse,
    LibraryRefreshResponse,
    LibraryScanResponse,
    LibraryStatsResponse,
    MovieStats,
    MusicStats,
    ShowStats,
)
from . import connect_to_plex, mcp

if TYPE_CHECKING:
    from plexapi.library import Library


def get_plex_headers(plex: PlexServer) -> dict[str, Any]:
    """Get standard Plex headers for HTTP requests"""
    return {"X-Plex-Token": plex._token, "Accept": "application/json"}


async def async_get_json(
    session: ClientSession, url: str, headers: dict[str, Any]
) -> dict[str, Any]:
    """Helper function to make async HTTP requests"""
    async with session.get(url, headers=headers) as response:
        return await response.json()


@mcp.tool(
    name="library_list",
    description="List all available libraries on the Plex server",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def library_list() -> LibraryListResponse | ErrorResponse:
    """List all available libraries on the Plex server."""
    try:
        plex = connect_to_plex()
        plex_library: Library = plex.library
        libraries = plex_library.sections()

        if not libraries:
            return LibraryListResponse(message="No libraries found on your Plex server.")

        libraries_dict = {}
        for lib in libraries:
            libraries_dict[lib.title] = LibraryInfo(
                type=lib.type,
                libraryId=str(lib.key),
                totalSize=lib.totalSize,
                uuid=lib.uuid,
                locations=lib.locations,
                updatedAt=lib.updatedAt.isoformat(),
            )

        return LibraryListResponse(libraries=libraries_dict)
    except Exception as e:
        return ErrorResponse(message=f"Error listing libraries: {str(e)}")


@mcp.tool(
    name="library_get_stats",
    description="Get statistics for a specific library",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def library_get_stats(library_name: str) -> LibraryStatsResponse | ErrorResponse:
    """Get statistics for a specific library.

    Args:
        library_name: Name of the library to get stats for
    """
    try:
        plex = connect_to_plex()
        base_url: str = str(plex._baseurl)
        headers = get_plex_headers(plex)

        async with aiohttp.ClientSession() as session:
            sections_url = urljoin(base_url, "library/sections")
            sections_data = await async_get_json(session, sections_url, headers)

            target_section = None
            for section in sections_data["MediaContainer"]["Directory"]:
                if section["title"].lower() == library_name.lower():
                    target_section = section
                    break

            if not target_section:
                return ErrorResponse(message=f"Library '{library_name}' not found")

            section_id = target_section["key"]
            library_type = target_section["type"]

            # Prepare URLs for concurrent requests
            all_items_url = urljoin(base_url, f"library/sections/{section_id}/all")
            unwatched_url = urljoin(base_url, f"library/sections/{section_id}/all?unwatched=1")

            # Make concurrent requests for all and unwatched items
            all_data, unwatched_data = await asyncio.gather(
                async_get_json(session, all_items_url, headers),
                async_get_json(session, unwatched_url, headers),
            )
            all_data = all_data["MediaContainer"]
            unwatched_data = unwatched_data["MediaContainer"]

            if library_type == "movie":
                genres: dict[str, int] = {}
                directors: dict[str, int] = {}
                studios: dict[str, int] = {}
                decades: dict[int, int] = {}

                for movie in all_data.get("Metadata", []):
                    for genre in movie.get("Genre", []):
                        genre_name = genre["tag"]
                        genres[genre_name] = genres.get(genre_name, 0) + 1

                    for director in movie.get("Director", []):
                        director_name = director["tag"]
                        directors[director_name] = directors.get(director_name, 0) + 1

                    studio = movie.get("studio")
                    if studio:
                        studios[studio] = studios.get(studio, 0) + 1

                    year = movie.get("year")
                    if year:
                        decade = (year // 10) * 10
                        decades[decade] = decades.get(decade, 0) + 1

                movie_stats = MovieStats(
                    count=all_data.get("size", 0),
                    unwatched=unwatched_data.get("size", 0),
                    topGenres=dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]) if genres else None,
                    topDirectors=dict(sorted(directors.items(), key=lambda x: x[1], reverse=True)[:5]) if directors else None,
                    topStudios=dict(sorted(studios.items(), key=lambda x: x[1], reverse=True)[:5]) if studios else None,
                    byDecade=dict(sorted(decades.items())) if decades else None,
                )

                return LibraryStatsResponse(
                    name=target_section["title"],
                    type=library_type,
                    totalItems=target_section.get("totalSize", 0),
                    movieStats=movie_stats,
                )

            elif library_type == "show":
                seasons_url = urljoin(base_url, f"library/sections/{section_id}/all?type=3")
                episodes_url = urljoin(base_url, f"library/sections/{section_id}/all?type=4")

                seasons_data, episodes_data = await asyncio.gather(
                    async_get_json(session, seasons_url, headers),
                    async_get_json(session, episodes_url, headers),
                )
                seasons_data = seasons_data["MediaContainer"]
                episodes_data = episodes_data["MediaContainer"]

                genres = {}
                studios = {}
                decades = {}

                for show in all_data.get("Metadata", []):
                    for genre in show.get("Genre", []):
                        genre_name = genre["tag"]
                        genres[genre_name] = genres.get(genre_name, 0) + 1

                    studio = show.get("studio")
                    if studio:
                        studios[studio] = studios.get(studio, 0) + 1

                    year = show.get("year")
                    if year:
                        decade = (year // 10) * 10
                        decades[decade] = decades.get(decade, 0) + 1

                show_stats = ShowStats(
                    shows=all_data.get("size", 0),
                    seasons=seasons_data.get("size", 0),
                    episodes=episodes_data.get("size", 0),
                    unwatchedShows=unwatched_data.get("size", 0),
                    topGenres=dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]) if genres else None,
                    topStudios=dict(sorted(studios.items(), key=lambda x: x[1], reverse=True)[:5]) if studios else None,
                    byDecade=dict(sorted(decades.items())) if decades else None,
                )

                return LibraryStatsResponse(
                    name=target_section["title"],
                    type=library_type,
                    totalItems=target_section.get("totalSize", 0),
                    showStats=show_stats,
                )

            elif library_type == "artist":
                total_tracks = 0
                total_albums = 0
                total_plays = 0

                all_genres: dict[str, int] = {}
                all_years: dict[int, int] = {}
                top_artists: dict[str, int] = {}
                top_albums: dict[str, int] = {}
                audio_formats: dict[str, int] = {}

                for artist in all_data.get("Metadata", []):
                    artist_id = artist.get("ratingKey")
                    artist_name = artist.get("title", "")

                    if not artist_id:
                        continue

                    artist_view_count = 0
                    artist_albums = set()
                    artist_track_count = 0

                    artist_tracks_url = urljoin(
                        base_url, f"library/sections/{section_id}/all?artist.id={artist_id}&type=10"
                    )
                    artist_tracks_data = await async_get_json(session, artist_tracks_url, headers)

                    if (
                        "MediaContainer" in artist_tracks_data
                        and "Metadata" in artist_tracks_data["MediaContainer"]
                    ):
                        for track in artist_tracks_data["MediaContainer"]["Metadata"]:
                            artist_track_count += 1

                            track_views = track.get("viewCount", 0)
                            artist_view_count += track_views
                            total_plays += track_views

                            album_title = track.get("parentTitle")
                            if album_title:
                                artist_albums.add(album_title)

                                album_key = f"{artist_name} - {album_title}"
                                if album_key not in top_albums:
                                    top_albums[album_key] = 0
                                top_albums[album_key] += track_views

                            if "Genre" in track:
                                for genre in track.get("Genre", []):
                                    genre_name = genre["tag"]
                                    all_genres[genre_name] = all_genres.get(genre_name, 0) + 1

                            year = track.get("parentYear") or track.get("year")
                            if year:
                                all_years[year] = all_years.get(year, 0) + 1

                            if (
                                "Media" in track
                                and track["Media"]
                                and "audioCodec" in track["Media"][0]
                            ):
                                audio_codec = track["Media"][0]["audioCodec"]
                                audio_formats[audio_codec] = audio_formats.get(audio_codec, 0) + 1

                    if artist_track_count > 0:
                        top_artists[artist_name] = artist_view_count

                    total_tracks += artist_track_count
                    total_albums += len(artist_albums)

                music_stats = MusicStats(
                    count=all_data.get("size", 0),
                    totalTracks=total_tracks,
                    totalAlbums=total_albums,
                    totalPlays=total_plays,
                    topGenres=dict(sorted(all_genres.items(), key=lambda x: x[1], reverse=True)[:10]) if all_genres else None,
                    topArtists=dict(sorted(top_artists.items(), key=lambda x: x[1], reverse=True)[:10]) if top_artists else None,
                    topAlbums=dict(sorted(top_albums.items(), key=lambda x: x[1], reverse=True)[:10]) if top_albums else None,
                    byYear=dict(sorted(all_years.items())) if all_years else None,
                    audioFormats=audio_formats if audio_formats else None,
                )

                return LibraryStatsResponse(
                    name=target_section["title"],
                    type=library_type,
                    totalItems=target_section.get("totalSize", 0),
                    musicStats=music_stats,
                )

            return LibraryStatsResponse(
                name=target_section["title"],
                type=library_type,
                totalItems=target_section.get("totalSize", 0),
            )

    except Exception as e:
        return ErrorResponse(message=f"Error getting library stats: {str(e)}")


@mcp.tool(
    name="library_refresh",
    description="Refresh a specific library or all libraries",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=True)
)
async def library_refresh(library_name: str | None = None) -> LibraryRefreshResponse | ErrorResponse:
    """Refresh a specific library or all libraries.

    Args:
        library_name: Optional name of the library to refresh (refreshes all if None)
    """
    try:
        plex = connect_to_plex()

        if library_name:
            section = None
            all_sections = plex.library.sections()

            for s in all_sections:
                if s.title.lower() == library_name.lower():
                    section = s
                    break

            if not section:
                return ErrorResponse(
                    message=f"Library '{library_name}' not found. Available libraries: {', '.join([s.title for s in all_sections])}"
                )

            section.refresh()
            return LibraryRefreshResponse(
                success=True,
                message=f"Refreshing library '{section.title}'. This may take some time.",
            )
        else:
            plex.library.refresh()
            return LibraryRefreshResponse(
                success=True,
                message="Refreshing all libraries. This may take some time."
            )
    except Exception as e:
        return ErrorResponse(message=f"Error refreshing library: {str(e)}")


@mcp.tool(
    name="library_scan",
    description="Scan a specific library or part of a library",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=True)
)
async def library_scan(library_name: str, path: str | None = None) -> LibraryScanResponse | ErrorResponse:
    """Scan a specific library or part of a library.

    Args:
        library_name: Name of the library to scan
        path: Optional specific path to scan within the library
    """
    try:
        plex = connect_to_plex()

        section = None
        all_sections = plex.library.sections()

        for s in all_sections:
            if s.title.lower() == library_name.lower():
                section = s
                break

        if not section:
            return ErrorResponse(
                message=f"Library '{library_name}' not found. Available libraries: {', '.join([s.title for s in all_sections])}"
            )

        if path:
            try:
                section.update(path=path)
                return LibraryScanResponse(
                    success=True,
                    message=f"Scanning path '{path}' in library '{section.title}'. This may take some time.",
                )
            except NotFound:
                return ErrorResponse(message=f"Path '{path}' not found in library '{section.title}'.")
        else:
            section.update()
            return LibraryScanResponse(
                success=True,
                message=f"Scanning library '{section.title}'. This may take some time.",
            )
    except Exception as e:
        return ErrorResponse(message=f"Error scanning library: {str(e)}")


@mcp.tool(
    name="library_get_details",
    description="Get detailed information about a specific library, including folder paths and settings",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def library_get_details(library_name: str) -> LibraryDetailsResponse | ErrorResponse:
    """Get detailed information about a specific library, including folder paths and settings.

    Args:
        library_name: Name of the library to get details for
    """
    try:
        plex = connect_to_plex()

        all_sections = plex.library.sections()
        target_section = None

        for section in all_sections:
            if section.title.lower() == library_name.lower():
                target_section = section
                break

        if not target_section:
            return ErrorResponse(
                message=f"Library '{library_name}' not found. Available libraries: {', '.join([s.title for s in all_sections])}"
            )

        data = target_section._data

        scanner_settings: dict[str, str] | None = None
        if "scannerSettings" in data:
            temp_scanner = {}
            for setting in data["scannerSettings"]:
                if "value" in setting:
                    temp_scanner[setting.get("key", "unknown")] = setting["value"]
            if temp_scanner:
                scanner_settings = temp_scanner

        agent_settings: dict[str, str] | None = None
        if "agentSettings" in data:
            temp_agent = {}
            for setting in data["agentSettings"]:
                if "value" in setting:
                    temp_agent[setting.get("key", "unknown")] = setting["value"]
            if temp_agent:
                agent_settings = temp_agent

        advanced_settings: dict[str, str] | None = None
        if "advancedSettings" in data:
            temp_advanced = {}
            for setting in data["advancedSettings"]:
                if "value" in setting:
                    temp_advanced[setting.get("key", "unknown")] = setting["value"]
            if temp_advanced:
                advanced_settings = temp_advanced

        return LibraryDetailsResponse(
            name=target_section.title,
            type=target_section.type,
            uuid=target_section.uuid,
            totalItems=target_section.totalSize,
            locations=target_section.locations,
            agent=target_section.agent,
            scanner=target_section.scanner,
            language=target_section.language,
            scannerSettings=scanner_settings,
            agentSettings=agent_settings,
            advancedSettings=advanced_settings,
        )
    except Exception as e:
        return ErrorResponse(message=f"Error getting library details: {str(e)}")


@mcp.tool(
    name="library_get_recently_added",
    description="Get recently added media across all libraries or in a specific library",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def library_get_recently_added(count: int = 50, library_name: str | None = None) -> LibraryRecentlyAddedResponse | ErrorResponse:
    """Get recently added media across all libraries or in a specific library.

    Args:
        count: Number of items to return (default: 50)
        library_name: Optional library name to limit results to
    """
    try:
        plex = connect_to_plex()

        if library_name:
            section = None
            all_sections = plex.library.sections()

            for s in all_sections:
                if s.title.lower() == library_name.lower():
                    section = s
                    break

            if not section:
                return ErrorResponse(
                    message=f"Library '{library_name}' not found. Available libraries: {', '.join([s.title for s in all_sections])}"
                )

            recent = section.recentlyAdded(maxresults=count)
        else:
            recent = plex.library.recentlyAdded()
            if recent:
                try:
                    from datetime import datetime

                    recent = sorted(
                        recent, key=lambda x: getattr(x, "addedAt", datetime.min), reverse=True
                    )[:count]
                except Exception:
                    recent = recent[:count]

        if not recent:
            return LibraryRecentlyAddedResponse(
                count=0,
                requestedCount=count,
                library=library_name if library_name else "All Libraries",
                items={}
            )

        items_by_type: dict[str, list[dict[str, str | int]]] = {}

        for item in recent:
            item_type = getattr(item, "type", "unknown")
            if item_type not in items_by_type:
                items_by_type[item_type] = []

            try:
                added_at = str(getattr(item, "addedAt", "Unknown date"))

                if item_type == "movie" or item_type == "show":
                    items_by_type[item_type].append(
                        {
                            "title": item.title,
                            "year": str(getattr(item, "year", "")),
                            "addedAt": added_at,
                        }
                    )

                elif item_type == "season":
                    items_by_type[item_type].append(
                        {
                            "showTitle": getattr(item, "parentTitle", "Unknown Show"),
                            "seasonNumber": getattr(item, "index", "?"),
                            "addedAt": added_at,
                        }
                    )

                elif item_type == "episode":
                    items_by_type[item_type].append(
                        {
                            "showTitle": getattr(item, "grandparentTitle", "Unknown Show"),
                            "seasonNumber": getattr(item, "parentIndex", "?"),
                            "episodeNumber": getattr(item, "index", "?"),
                            "title": item.title,
                            "addedAt": added_at,
                        }
                    )

                elif item_type == "artist":
                    items_by_type[item_type].append({"title": item.title, "addedAt": added_at})

                elif item_type == "album":
                    items_by_type[item_type].append(
                        {
                            "artist": getattr(item, "parentTitle", "Unknown Artist"),
                            "title": item.title,
                            "addedAt": added_at,
                        }
                    )

                elif item_type == "track":
                    items_by_type[item_type].append(
                        {
                            "artist": getattr(item, "grandparentTitle", "Unknown Artist"),
                            "album": getattr(item, "parentTitle", "Unknown Album"),
                            "title": item.title,
                            "addedAt": added_at,
                        }
                    )

                else:
                    items_by_type[item_type].append(
                        {"title": getattr(item, "title", "Unknown"), "addedAt": added_at}
                    )

            except Exception as format_error:
                items_by_type[item_type].append(
                    {"title": getattr(item, "title", "Unknown"), "error": str(format_error)}
                )

        return LibraryRecentlyAddedResponse(
            count=len(recent),
            requestedCount=count,
            library=library_name if library_name else "All Libraries",
            items=items_by_type
        )
    except Exception as e:
        return ErrorResponse(message=f"Error getting recently added items: {str(e)}")


@mcp.tool(
    name="library_get_contents",
    description="Get the full contents of a specific library",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def library_get_contents(library_name: str) -> LibraryContentsResponse | ErrorResponse:
    """Get the full contents of a specific library.

    Args:
        library_name: Name of the library to get contents from
    """
    try:
        plex = connect_to_plex()
        base_url: str = str(plex._baseurl)
        headers = get_plex_headers(plex)

        async with aiohttp.ClientSession() as session:
            sections_url = urljoin(base_url, "library/sections")
            sections_data = await async_get_json(session, sections_url, headers)

            target_section = None
            for section in sections_data["MediaContainer"]["Directory"]:
                if section["title"].lower() == library_name.lower():
                    target_section = section
                    break

            if not target_section:
                return ErrorResponse(message=f"Library '{library_name}' not found")

            section_id = target_section["key"]
            library_type = target_section["type"]

            all_items_url = urljoin(base_url, f"library/sections/{section_id}/all")
            all_data = await async_get_json(session, all_items_url, headers)
            all_data = all_data["MediaContainer"]

            items: list[dict[str, str | int | bool | dict | None]] = []

            if library_type == "movie":
                for item in all_data.get("Metadata", []):
                    year = item.get("year", "Unknown")
                    duration = item.get("duration", 0)
                    hours, remainder = divmod(duration // 1000, 3600)
                    minutes, _ = divmod(remainder, 60)

                    media_info = {}
                    if "Media" in item:
                        media = item["Media"][0] if item["Media"] else {}
                        resolution = media.get("videoResolution", "")
                        codec = media.get("videoCodec", "")
                        if resolution and codec:
                            media_info = {"resolution": resolution, "codec": codec}

                    watched = item.get("viewCount", 0) > 0

                    items.append(
                        {
                            "title": item.get("title", ""),
                            "year": year,
                            "duration": {"hours": hours, "minutes": minutes},
                            "mediaInfo": media_info,
                            "watched": watched,
                        }
                    )

            elif library_type == "show":
                show_urls = [
                    (item["ratingKey"], urljoin(base_url, f"library/metadata/{item['ratingKey']}"))
                    for item in all_data.get("Metadata", [])
                ]
                show_responses = await asyncio.gather(
                    *[async_get_json(session, url, headers) for _, url in show_urls]
                )

                for item, show_data in zip(
                    all_data.get("Metadata", []), show_responses, strict=False
                ):
                    show_data = show_data["MediaContainer"]["Metadata"][0]

                    year = item.get("year", "Unknown")
                    season_count = show_data.get("childCount", 0)
                    episode_count = show_data.get("leafCount", 0)
                    watched = (
                        episode_count > 0 and show_data.get("viewedLeafCount", 0) == episode_count
                    )

                    items.append(
                        {
                            "title": item.get("title", ""),
                            "year": year,
                            "seasonCount": season_count,
                            "episodeCount": episode_count,
                            "watched": watched,
                        }
                    )

            elif library_type == "artist":
                artists_info = {}

                for artist in all_data.get("Metadata", []):
                    artist_id = artist.get("ratingKey")
                    artist_name = artist.get("title", "")

                    if not artist_id:
                        continue

                    orig_view_count = artist.get("viewCount", 0)
                    orig_skip_count = artist.get("skipCount", 0)

                    artist_tracks_url = urljoin(
                        base_url, f"library/sections/{section_id}/all?artist.id={artist_id}&type=10"
                    )
                    artist_tracks_data = await async_get_json(session, artist_tracks_url, headers)

                    if artist_name not in artists_info:
                        artists_info[artist_name] = {
                            "title": artist_name,
                            "albums": set(),
                            "trackCount": 0,
                            "viewCount": 0,
                            "skipCount": 0,
                        }

                    track_view_count = 0
                    track_skip_count = 0
                    if (
                        "MediaContainer" in artist_tracks_data
                        and "Metadata" in artist_tracks_data["MediaContainer"]
                    ):
                        for track in artist_tracks_data["MediaContainer"]["Metadata"]:
                            artists_info[artist_name]["trackCount"] += 1

                            if "parentTitle" in track and track["parentTitle"]:
                                artists_info[artist_name]["albums"].add(track["parentTitle"])

                            track_view_count += track.get("viewCount", 0)
                            track_skip_count += track.get("skipCount", 0)

                    artists_info[artist_name]["viewCount"] = (
                        track_view_count if track_view_count > 0 else orig_view_count
                    )
                    artists_info[artist_name]["skipCount"] = (
                        track_skip_count if track_skip_count > 0 else orig_skip_count
                    )

                for _artist_name, info in artists_info.items():
                    items.append(
                        {
                            "title": info["title"],
                            "albumCount": len(info["albums"]),
                            "trackCount": info["trackCount"],
                            "viewCount": info["viewCount"],
                            "skipCount": info["skipCount"],
                        }
                    )

            else:
                for item in all_data.get("Metadata", []):
                    items.append({"title": item.get("title", "")})

            return LibraryContentsResponse(
                name=target_section["title"],
                type=library_type,
                totalItems=all_data.get("size", 0),
                items=items
            )

    except Exception as e:
        return ErrorResponse(message=f"Error getting library contents: {str(e)}")
