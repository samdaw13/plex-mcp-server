"""Pydantic models for MCP tool parameters and responses."""

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# CLIENT MODELS - Responses
# ============================================================================

class ClientInfo(BaseModel):
    """Detailed information about a Plex client."""
    name: str
    device: str
    model: str
    product: str
    version: str
    platform: str
    state: str
    machineIdentifier: str
    address: str
    protocolCapabilities: list[str]


class ClientListResponse(BaseModel):
    """Response from client_list tool."""
    status: str
    message: str
    count: int
    clients: list[ClientInfo] | list[str]


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str


# ============================================================================
# CLIENT MODELS - Request Parameters
# ============================================================================

class ClientListRequest(BaseModel):
    """Parameters for the client_list tool."""
    include_details: bool = Field(
        default=True,
        description="Whether to include detailed information about each client"
    )


class ClientGetDetailsRequest(BaseModel):
    """Parameters for the client_get_details tool."""
    client_name: str = Field(
        ...,
        description="Name of the client to get details for"
    )


class ClientGetTimelinesRequest(BaseModel):
    """Parameters for the client_get_timelines tool."""
    client_name: str = Field(
        ...,
        description="Name of the client to get timeline for"
    )


class ClientStartPlaybackRequest(BaseModel):
    """Parameters for the client_start_playback tool."""
    media_title: str = Field(
        ...,
        description="Title of the media to play"
    )
    client_name: str | None = Field(
        default=None,
        description="Optional name of the client to play on (will prompt if not provided)"
    )
    offset: int = Field(
        default=0,
        description="Optional time offset in milliseconds to start from"
    )
    library_name: str | None = Field(
        default=None,
        description="Optional name of the library to search in"
    )
    use_external_player: bool = Field(
        default=False,
        description="Whether to use the client's external player"
    )


class ClientControlPlaybackRequest(BaseModel):
    """Parameters for the client_control_playback tool."""
    client_name: str = Field(
        ...,
        description="Name of the client to control"
    )
    action: str = Field(
        ...,
        description="Action to perform (play, pause, stop, skipNext, skipPrevious, stepForward, stepBack, seekTo, seekForward, seekBack, mute, unmute, setVolume)"
    )
    parameter: int | None = Field(
        default=None,
        description="Parameter for actions that require it (like setVolume or seekTo)"
    )
    media_type: str = Field(
        default="video",
        description="Type of media being controlled ('video', 'music', or 'photo')"
    )


class ClientNavigateRequest(BaseModel):
    """Parameters for the client_navigate tool."""
    client_name: str = Field(
        ...,
        description="Name of the client to navigate"
    )
    action: str = Field(
        ...,
        description="Navigation action to perform (moveUp, moveDown, moveLeft, moveRight, select, back, home, contextMenu)"
    )


class ClientSetStreamsRequest(BaseModel):
    """Parameters for the client_set_streams tool."""
    client_name: str = Field(
        ...,
        description="Name of the client to set streams for"
    )
    audio_stream_id: str | None = Field(
        default=None,
        description="ID of the audio stream to switch to"
    )
    subtitle_stream_id: str | None = Field(
        default=None,
        description="ID of the subtitle stream to switch to, use '0' to disable"
    )
    video_stream_id: str | None = Field(
        default=None,
        description="ID of the video stream to switch to"
    )


# Additional Client Response Models
class ClientDetailsResponse(BaseModel):
    """Response from client_get_details tool."""
    status: str
    client: dict[str, str | list[str]]


class TimelineInfo(BaseModel):
    """Timeline information for a client."""
    state: str
    time: int
    duration: int
    progress: float
    title: str | None = None
    type: str | None = None


class ClientTimelineResponse(BaseModel):
    """Response from client_get_timelines tool."""
    model_config = {"extra": "allow"}  # Allow extra fields

    status: str
    message: str | None = None
    client_name: str | None = None
    source: str | None = None
    timeline: dict[str, str | int | float | None] | None = None


class ActiveClientMedia(BaseModel):
    """Media information for active client."""
    title: str
    type: str
    show: str | None = None
    season: str | None = None
    seasonEpisode: str | None = None
    year: str | None = None


class ActiveClientInfo(BaseModel):
    """Active client with playback status."""
    name: str
    device: str
    product: str
    platform: str
    state: str
    user: str
    media: ActiveClientMedia
    progress: float | None = None
    transcoding: bool


class ActiveClientsResponse(BaseModel):
    """Response from client_get_active tool."""
    model_config = {"extra": "allow"}  # Allow extra fields

    status: str
    message: str
    count: int
    active_clients: list[dict[str, str | int | float | bool | dict | None]]


class PlaybackResponse(BaseModel):
    """Generic playback operation response."""
    model_config = {"extra": "allow"}  # Allow extra fields

    status: str
    message: str | None = None
    client: str | None = None
    action: str | None = None
    parameter: int | None = None
    timeline: dict[str, str | int | bool | None] | None = None
    media: dict[str, str | int | None] | None = None
    offset: int | None = None
    count: int | None = None
    results: list[dict[str, str | int | None]] | None = None
    available_clients: list[dict[str, str | int]] | None = None
    changes: dict[str, str | None] | None = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    model_config = {"extra": "allow"}  # Allow extra fields

    status: str
    message: str
    client: str | None = None
    action: str | None = None
    parameter: int | None = None
    timeline: dict[str, str | int | bool | None] | None = None
    changes: dict[str, str | None] | None = None

# ============================================================================
# COLLECTION MODELS
# ============================================================================

class CollectionInfo(BaseModel):
    """Information about a collection."""
    title: str
    summary: str | None = None
    is_smart: bool
    ID: int
    items: int


class LibraryCollections(BaseModel):
    """Collections within a library."""
    type: str
    collections_count: int
    collections: list[CollectionInfo]


class CollectionListResponse(BaseModel):
    """Response from collection_list tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    collections: list[CollectionInfo] | dict[str, LibraryCollections] | None = None


class PossibleMatch(BaseModel):
    """Possible match for a media item."""
    title: str
    id: int
    type: str
    year: int | None = None


class CollectionCreateResponse(BaseModel):
    """Response from collection_create tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    created: bool | None = None
    title: str | None = None
    id: int | None = None
    library: str | None = None
    items_added: int | None = None
    items_not_found: list[str] | None = None
    possible_matches: list[PossibleMatch] | None = None


class CollectionAddResponse(BaseModel):
    """Response from collection_add_to tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    added: bool | None = None
    title: str | None = None
    items_added: list[str] | None = None
    items_already_in_collection: list[str] | None = None
    items_not_found: list[str] | None = None
    total_items: int | None = None
    possible_matches: list[PossibleMatch] | None = None
    multiple_collections: list[dict[str, str | int]] | None = None


class CollectionRemoveResponse(BaseModel):
    """Response from collection_remove_from tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    removed: bool | None = None
    title: str | None = None
    items_removed: list[str] | None = None
    items_not_found: list[str] | None = None
    remaining_items: int | None = None
    collection_title: str | None = None
    collection_id: int | None = None
    current_items: list[dict[str, str | int]] | None = None
    multiple_collections: list[dict[str, str | int]] | None = None


class CollectionDeleteResponse(BaseModel):
    """Response from collection_delete tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    deleted: bool | None = None
    title: str | None = None
    multiple_collections: list[dict[str, str | int]] | None = None


class CollectionEditResponse(BaseModel):
    """Response from collection_edit tool."""
    model_config = {"extra": "allow"}
    status: str = "success"
    updated: bool | None = None
    title: str | None = None
    changes: list[str] | None = None
    message: str | None = None
    multiple_collections: list[dict[str, str | int]] | None = None


# ============================================================================
# LIBRARY MODELS
# ============================================================================

class LibraryInfo(BaseModel):
    """Information about a library."""
    type: str
    libraryId: str
    totalSize: int
    uuid: str
    locations: list[str]
    updatedAt: str


class LibraryListResponse(BaseModel):
    """Response from library_list tool."""
    model_config = {"extra": "allow"}
    libraries: dict[str, LibraryInfo] | None = None
    message: str | None = None


class MovieStats(BaseModel):
    """Statistics for movie library."""
    count: int
    unwatched: int
    topGenres: dict[str, int] | None = None
    topDirectors: dict[str, int] | None = None
    topStudios: dict[str, int] | None = None
    byDecade: dict[int, int] | None = None


class ShowStats(BaseModel):
    """Statistics for TV show library."""
    shows: int
    seasons: int
    episodes: int
    unwatchedShows: int
    topGenres: dict[str, int] | None = None
    topStudios: dict[str, int] | None = None
    byDecade: dict[int, int] | None = None


class MusicStats(BaseModel):
    """Statistics for music library."""
    count: int
    totalTracks: int
    totalAlbums: int
    totalPlays: int
    topGenres: dict[str, int] | None = None
    topArtists: dict[str, int] | None = None
    topAlbums: dict[str, int] | None = None
    byYear: dict[int, int] | None = None
    audioFormats: dict[str, int] | None = None


class LibraryStatsResponse(BaseModel):
    """Response from library_get_stats tool."""
    model_config = {"extra": "allow"}
    name: str
    type: str
    totalItems: int
    movieStats: MovieStats | None = None
    showStats: ShowStats | None = None
    musicStats: MusicStats | None = None


class LibraryRefreshResponse(BaseModel):
    """Response from library_refresh tool."""
    model_config = {"extra": "allow"}
    success: bool
    message: str


class LibraryScanResponse(BaseModel):
    """Response from library_scan tool."""
    model_config = {"extra": "allow"}
    success: bool
    message: str


class LibraryDetailsResponse(BaseModel):
    """Response from library_get_details tool."""
    model_config = {"extra": "allow"}
    name: str
    type: str
    uuid: str
    totalItems: int
    locations: list[str]
    agent: str
    scanner: str
    language: str
    scannerSettings: dict[str, str] | None = None
    agentSettings: dict[str, str] | None = None
    advancedSettings: dict[str, str] | None = None


class RecentlyAddedItem(BaseModel):
    """A recently added media item."""
    title: str
    addedAt: str
    year: str | None = None
    showTitle: str | None = None
    seasonNumber: int | str | None = None
    episodeNumber: int | str | None = None
    artist: str | None = None
    album: str | None = None
    error: str | None = None


class LibraryRecentlyAddedResponse(BaseModel):
    """Response from library_get_recently_added tool."""
    model_config = {"extra": "allow"}
    count: int
    requestedCount: int
    library: str
    items: dict[str, list[dict[str, Any] | RecentlyAddedItem]]


class LibraryContentItem(BaseModel):
    """An item in a library."""
    title: str
    year: str | int | None = None
    duration: dict[str, int] | None = None
    mediaInfo: dict[str, str] | None = None
    watched: bool | None = None
    seasonCount: int | None = None
    episodeCount: int | None = None
    albumCount: int | None = None
    trackCount: int | None = None
    viewCount: int | None = None
    skipCount: int | None = None


class LibraryContentsResponse(BaseModel):
    """Response from library_get_contents tool."""
    model_config = {"extra": "allow"}
    name: str
    type: str
    totalItems: int
    items: list[LibraryContentItem | dict[str, str | int | bool | dict | None]]


# ============================================================================
# MEDIA, SERVER, SESSIONS, USER, PLAYLIST MODELS
# ============================================================================

# Generic models that can be reused across modules
class ListResponse(BaseModel):
    """Generic list response."""
    status: str
    message: str | None = None
    count: int | None = None
    items: list[dict[str, str | int | float | bool | list | dict | None]] | list[str]


class OperationResponse(BaseModel):
    """Generic operation response with flexible data."""
    status: str
    message: str
    data: dict[str, str | int | float | bool | list | dict | None] | None = None


class InfoResponse(BaseModel):
    """Generic info response."""
    status: str
    info: dict[str, str | int | float | bool | list | dict | None]


# These generic models can handle most tool responses
# Individual tools can use these or create more specific ones as needed
