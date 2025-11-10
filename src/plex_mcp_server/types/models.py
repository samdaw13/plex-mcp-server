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
    machine_identifier: str
    address: str
    protocol_capabilities: list[str]


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
        default=True, description="Whether to include detailed information about each client"
    )


class ClientGetDetailsRequest(BaseModel):
    """Parameters for the client_get_details tool."""

    client_name: str = Field(..., description="Name of the client to get details for")


class ClientGetTimelinesRequest(BaseModel):
    """Parameters for the client_get_timelines tool."""

    client_name: str = Field(..., description="Name of the client to get timeline for")


class ClientStartPlaybackRequest(BaseModel):
    """Parameters for the client_start_playback tool."""

    media_title: str = Field(..., description="Title of the media to play")
    client_name: str | None = Field(
        default=None,
        description="Optional name of the client to play on (will prompt if not provided)",
    )
    offset: int = Field(default=0, description="Optional time offset in milliseconds to start from")
    library_name: str | None = Field(
        default=None, description="Optional name of the library to search in"
    )
    use_external_player: bool = Field(
        default=False, description="Whether to use the client's external player"
    )


class ClientControlPlaybackRequest(BaseModel):
    """Parameters for the client_control_playback tool."""

    client_name: str = Field(..., description="Name of the client to control")
    action: str = Field(
        ...,
        description="Action to perform (play, pause, stop, skipNext, skipPrevious, stepForward, stepBack, seekTo, seekForward, seekBack, mute, unmute, setVolume)",
    )
    parameter: int | None = Field(
        default=None, description="Parameter for actions that require it (like setVolume or seekTo)"
    )
    media_type: str = Field(
        default="video", description="Type of media being controlled ('video', 'music', or 'photo')"
    )


class ClientNavigateRequest(BaseModel):
    """Parameters for the client_navigate tool."""

    client_name: str = Field(..., description="Name of the client to navigate")
    action: str = Field(
        ...,
        description="Navigation action to perform (moveUp, moveDown, moveLeft, moveRight, select, back, home, contextMenu)",
    )


class ClientSetStreamsRequest(BaseModel):
    """Parameters for the client_set_streams tool."""

    client_name: str = Field(..., description="Name of the client to set streams for")
    audio_stream_id: str | None = Field(
        default=None, description="ID of the audio stream to switch to"
    )
    subtitle_stream_id: str | None = Field(
        default=None, description="ID of the subtitle stream to switch to, use '0' to disable"
    )
    video_stream_id: str | None = Field(
        default=None, description="ID of the video stream to switch to"
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
    season_episode: str | None = None
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
    active_clients: list[dict[str, Any]]


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
    library_id: str
    total_size: int
    uuid: str
    locations: list[str]
    updated_at: str


class LibraryListResponse(BaseModel):
    """Response from library_list tool."""

    model_config = {"extra": "allow"}
    libraries: dict[str, LibraryInfo] | None = None
    message: str | None = None


class MovieStats(BaseModel):
    """Statistics for movie library."""

    count: int
    unwatched: int
    top_genres: dict[str, int] | None = None
    top_directors: dict[str, int] | None = None
    top_studios: dict[str, int] | None = None
    by_decade: dict[int, int] | None = None


class ShowStats(BaseModel):
    """Statistics for TV show library."""

    shows: int
    seasons: int
    episodes: int
    unwatched_shows: int
    top_genres: dict[str, int] | None = None
    top_studios: dict[str, int] | None = None
    by_decade: dict[int, int] | None = None


class MusicStats(BaseModel):
    """Statistics for music library."""

    count: int
    total_tracks: int
    total_albums: int
    total_plays: int
    top_genres: dict[str, int] | None = None
    top_artists: dict[str, int] | None = None
    top_albums: dict[str, int] | None = None
    by_year: dict[int, int] | None = None
    audio_formats: dict[str, int] | None = None


class LibraryStatsResponse(BaseModel):
    """Response from library_get_stats tool."""

    model_config = {"extra": "allow"}
    name: str
    type: str
    total_items: int
    movie_stats: MovieStats | None = None
    show_stats: ShowStats | None = None
    music_stats: MusicStats | None = None


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
    total_items: int
    locations: list[str]
    agent: str
    scanner: str
    language: str
    scanner_settings: dict[str, str] | None = None
    agent_settings: dict[str, str] | None = None
    advanced_settings: dict[str, str] | None = None


class RecentlyAddedItem(BaseModel):
    """A recently added media item."""

    title: str
    added_at: str
    year: str | None = None
    show_title: str | None = None
    season_number: int | str | None = None
    episode_number: int | str | None = None
    artist: str | None = None
    album: str | None = None
    error: str | None = None


class LibraryRecentlyAddedResponse(BaseModel):
    """Response from library_get_recently_added tool."""

    model_config = {"extra": "allow"}
    count: int
    requested_count: int
    library: str
    items: dict[str, list[dict[str, Any] | RecentlyAddedItem]]


class LibraryContentItem(BaseModel):
    """An item in a library."""

    title: str
    year: str | int | None = None
    duration: dict[str, int] | None = None
    media_info: dict[str, str] | None = None
    watched: bool | None = None
    season_count: int | None = None
    episode_count: int | None = None
    album_count: int | None = None
    track_count: int | None = None
    view_count: int | None = None
    skip_count: int | None = None


class LibraryContentsResponse(BaseModel):
    """Response from library_get_contents tool."""

    model_config = {"extra": "allow"}
    name: str
    type: str
    total_items: int
    items: list[LibraryContentItem | dict[str, Any]]


# ============================================================================
# MEDIA MODELS
# ============================================================================


class SearchResultItem(BaseModel):
    """A single search result item."""

    model_config = {"extra": "allow"}
    title: str
    type: str
    rating_key: int | None = None
    year: int | None = None
    rating: float | str | None = None
    summary: str | None = None
    show_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    artist: str | None = None
    album: str | None = None
    track_number: int | None = None
    duration: int | None = None
    library: str | None = None
    resolution: str | None = None
    container: str | None = None
    codec: str | None = None
    audio_codec: str | None = None
    bitrate: int | None = None
    art: str | None = None
    thumb: str | None = None
    album_thumb: str | None = None
    artist_thumb: str | None = None


class MediaSearchResponse(BaseModel):
    """Response from media_search tool."""

    model_config = {"extra": "allow"}
    status: str
    message: str
    query: str | None = None
    content_type: str | None = None
    total_count: int
    results_by_type: dict[str, list[dict[str, Any] | SearchResultItem]]


class MediaDetailsResponse(BaseModel):
    """Response from media_get_details tool."""

    model_config = {"extra": "allow"}
    title: str | None = None
    type: str | None = None
    id: int | None = None
    added_at: str | None = None
    rating: float | str | None = None
    content_rating: str | None = None
    duration: str | None = None
    studio: str | None = None
    year: int | None = None
    summary: str | None = None
    seasons_count: int | None = None
    episodes_count: int | None = None
    seasons: list[dict[str, Any]] | None = None
    show_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    albums_count: int | None = None
    tracks_count: int | None = None
    albums: list[dict[str, Any]] | None = None
    artist: str | None = None
    artist_id: int | None = None
    album: str | None = None
    album_id: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    view_count: int | None = None
    skip_count: int | None = None
    genres: list[str] | None = None
    directors: list[str] | None = None
    writers: list[str] | None = None
    actors: list[str] | None = None
    error: str | None = None
    error_details: str | None = None


class MediaDetailsListResponse(BaseModel):
    """Response from media_get_details when multiple matches found."""

    model_config = {"extra": "allow"}
    items: list[dict[str, str | int | None]]


class MediaEditResponse(BaseModel):
    """Response from media_edit_metadata tool."""

    model_config = {"extra": "allow"}
    status: str = "success"
    message: str


class ArtworkInfo(BaseModel):
    """Information about artwork."""

    model_config = {"extra": "allow"}
    filename: str | None = None
    type: str | None = None
    url: str | None = None
    base64: str | None = None
    path: str | None = None
    versions_available: int | None = None
    error: str | None = None


class MediaArtworkResponse(BaseModel):
    """Response from media_get_artwork tool."""

    model_config = {"extra": "allow"}
    items: (
        dict[str, dict[str, str | int | None] | ArtworkInfo]
        | list[dict[str, str | int | None]]
        | None
    ) = None
    error: str | None = None


class MediaDeleteResponse(BaseModel):
    """Response from media_delete tool."""

    model_config = {"extra": "allow"}
    deleted: bool | None = None
    title: str | None = None
    type: str | None = None
    files_on_disk: list[str] | None = None
    error: str | None = None


class MediaSetArtworkResponse(BaseModel):
    """Response from media_set_artwork tool."""

    model_config = {"extra": "allow"}
    status: str = "success"
    message: str


class AvailableArtworkItem(BaseModel):
    """An available artwork item."""

    model_config = {"extra": "allow"}
    index: int
    provider: str
    url: str | None = None
    selected: bool
    rating_key: int | None = None


class MediaListArtworkResponse(BaseModel):
    """Response from media_list_available_artwork tool."""

    model_config = {"extra": "allow"}
    media_title: str | None = None
    media_id: int | None = None
    art_type: str
    count: int
    artwork: list[dict[str, str | int | bool | None] | AvailableArtworkItem]
    error: str | None = None


# ============================================================================
# PLAYLIST MODELS
# ============================================================================


class PlaylistInfo(BaseModel):
    """Information about a playlist."""

    model_config = {"extra": "allow"}
    title: str
    key: str | None = None
    rating_key: int | None = None
    type: str | None = None
    summary: str | None = None
    duration: int | None = None
    item_count: int | None = None
    error: str | None = None


class PlaylistListResponse(BaseModel):
    """Response from playlist_list tool."""

    model_config = {"extra": "allow"}
    items: list[dict[str, str | int | None] | PlaylistInfo]


class PlaylistCreateResponse(BaseModel):
    """Response from playlist_create tool."""

    model_config = {"extra": "allow"}
    status: str = "success"
    message: str
    data: dict[str, str | int] | None = None


class PlaylistEditResponse(BaseModel):
    """Response from playlist_edit tool."""

    model_config = {"extra": "allow"}
    updated: bool | None = None
    title: str | None = None
    changes: list[str] | None = None
    message: str | None = None
    items: list[dict[str, str | int]] | None = None


class PlaylistUploadPosterResponse(BaseModel):
    """Response from playlist_upload_poster tool."""

    model_config = {"extra": "allow"}
    updated: bool | None = None
    poster_source: str | None = None
    title: str | None = None
    items: list[dict[str, str | int]] | None = None


class PlaylistCopyResponse(BaseModel):
    """Response from playlist_copy_to_user tool."""

    model_config = {"extra": "allow"}
    status: str
    message: str
    matches: list[dict[str, str | int]] | None = None


class PlaylistAddResponse(BaseModel):
    """Response from playlist_add_to tool."""

    model_config = {"extra": "allow"}
    added: bool | None = None
    title: str | None = None
    items_added: list[str] | None = None
    items_not_found: list[str | dict[str, Any]] | None = None
    total_items: int | None = None
    items: dict[str, list[dict[str, str | int]]] | None = None


class PlaylistRemoveResponse(BaseModel):
    """Response from playlist_remove_from tool."""

    model_config = {"extra": "allow"}
    removed: bool | None = None
    title: str | None = None
    items_removed: list[str] | None = None
    items_not_found: list[str] | None = None
    remaining_items: int | None = None
    playlist_title: str | None = None
    playlist_id: int | None = None
    current_items: list[dict[str, str | int]] | None = None
    items: dict[str, list[dict[str, str | int]]] | None = None


class PlaylistDeleteResponse(BaseModel):
    """Response from playlist_delete tool."""

    model_config = {"extra": "allow"}
    deleted: bool | None = None
    title: str | None = None
    items: list[dict[str, str | int]] | None = None


class PlaylistItemInfo(BaseModel):
    """Information about a playlist item."""

    model_config = {"extra": "allow"}
    title: str
    type: str
    rating_key: int
    added_at: str | None = None
    duration: int | None = None
    thumb: str | None = None
    year: int | None = None
    show: str | None = None
    season: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None


class PlaylistContentsResponse(BaseModel):
    """Response from playlist_get_contents tool."""

    model_config = {"extra": "allow"}
    title: str
    id: int
    key: str
    type: str
    summary: str | None = None
    duration: int | None = None
    item_count: int
    items: list[dict[str, str | int | None] | PlaylistItemInfo]


# ============================================================================
# SERVER MODELS
# ============================================================================


class ServerLogsResponse(BaseModel):
    """Response from server_get_plex_logs tool."""

    model_config = {"extra": "allow"}
    logs: str
    error: str | None = None


class ServerInfoResponse(BaseModel):
    """Response from server_get_info tool."""

    model_config = {"extra": "allow"}
    status: str
    data: dict[str, Any] | None = None
    message: str | None = None


class BandwidthStats(BaseModel):
    """Bandwidth statistics entry."""

    model_config = {"extra": "allow"}
    account: str | None = None
    device_id: int | None = None
    device_name: str | None = None
    platform: str | None = None
    client_identifier: str | None = None
    at: str | None = None
    bytes: int | None = None
    is_local: bool | None = None
    timespan: int | None = None


class ServerBandwidthResponse(BaseModel):
    """Response from server_get_bandwidth tool."""

    model_config = {"extra": "allow"}
    status: str
    data: list[dict[str, str | int | bool | None] | BandwidthStats] | None = None
    message: str | None = None


class ResourceStats(BaseModel):
    """Resource usage statistics entry."""

    model_config = {"extra": "allow"}
    timestamp: str | None = None
    host_cpu_utilization: float | None = None
    host_memory_utilization: float | None = None
    process_cpu_utilization: float | None = None
    process_memory_utilization: float | None = None
    timespan: int | None = None


class ServerResourcesResponse(BaseModel):
    """Response from server_get_current_resources tool."""

    model_config = {"extra": "allow"}
    status: str
    data: list[dict[str, str | int | float | None] | ResourceStats] | None = None
    message: str | None = None


class ServerButlerTasksResponse(BaseModel):
    """Response from server_get_butler_tasks tool."""

    model_config = {"extra": "allow"}
    status: str
    data: list[dict[str, str | int | bool]] | None = None
    message: str | None = None
    raw_response: str | None = None


class AlertInfo(BaseModel):
    """Information about a server alert."""

    model_config = {"extra": "allow"}
    type: str
    title: str
    description: str
    text: str
    raw_data: Any | None = None
    error: str | None = None


class ServerAlertsResponse(BaseModel):
    """Response from server_get_alerts tool."""

    model_config = {"extra": "allow"}
    status: str
    data: list[dict[str, str | Any] | AlertInfo] | None = None
    message: str | None = None


class ServerRunButlerResponse(BaseModel):
    """Response from server_run_butler_task tool."""

    model_config = {"extra": "allow"}
    status: str
    message: str
    traceback: str | None = None


# ============================================================================
# SESSIONS MODELS
# ============================================================================


class SessionInfo(BaseModel):
    """Information about an active session."""

    model_config = {"extra": "allow"}
    session_id: int
    state: str
    player_name: str
    user: str
    content_type: str
    player: dict[str, str | None]
    progress: dict[str, float | int]
    content_description: str | None = None
    year: int | None = None
    media_info: dict[str, str] | None = None
    transcoding: dict[str, str | bool] | None = None


class SessionsActiveResponse(BaseModel):
    """Response from sessions_get_active tool."""

    model_config = {"extra": "allow"}
    status: str
    message: str
    sessions_count: int
    transcode_count: int | None = None
    direct_play_count: int | None = None
    total_bitrate_kbps: int | None = None
    sessions: list[dict[str, Any] | SessionInfo]


class HistoryEntry(BaseModel):
    """A playback history entry."""

    model_config = {"extra": "allow"}
    user: str
    viewed_at: str
    device: str


class MediaPlaybackHistoryResponse(BaseModel):
    """Response from sessions_get_media_playback_history tool."""

    model_config = {"extra": "allow"}
    status: str
    message: str | None = None
    media: dict[str, str | int] | None = None
    play_count: int
    history: list[dict[str, str] | HistoryEntry] | None = None
    last_viewed: str | None = None
    viewed_by: list[str] | None = None
    matches: list[dict[str, str | int]] | None = None


# ============================================================================
# USER MODELS
# ============================================================================


class UserInfo(BaseModel):
    """Information about a user."""

    model_config = {"extra": "allow"}
    role: str
    username: str
    email: str | None = None
    title: str | None = None
    libraries: list[str] | None = None


class UserSearchResponse(BaseModel):
    """Response from user_search_users tool."""

    model_config = {"extra": "allow"}
    search_term: str | None = None
    users_found: int | None = None
    users: list[dict[str, Any] | UserInfo] | None = None
    total_users: int | None = None
    owner: dict[str, str] | None = None
    shared_users: list[dict[str, str | None]] | None = None
    message: str | None = None


class UserDetailsResponse(BaseModel):
    """Response from user_get_info tool."""

    model_config = {"extra": "allow"}
    role: str
    username: str
    email: str | None = None
    title: str | None = None
    uuid: str | None = None
    auth_token: str | None = None
    subscription: dict[str, bool | list[str]] | None = None
    devices: list[dict[str, str]] | None = None
    joined_at: str | None = None
    id: int | None = None
    server_access: list[dict[str, str | list[str]]] | None = None


class OnDeckItem(BaseModel):
    """An on-deck media item."""

    model_config = {"extra": "allow"}
    type: str
    title: str
    show: str | None = None
    season: str | None = None
    year: str | None = None
    progress: float | None = None
    current_time: str | None = None
    total_time: str | None = None


class UserOnDeckResponse(BaseModel):
    """Response from user_get_on_deck tool."""

    model_config = {"extra": "allow"}
    username: str
    count: int
    items: list[dict[str, str | float | None] | OnDeckItem]
    message: str | None = None


class WatchHistoryItem(BaseModel):
    """A watch history item."""

    model_config = {"extra": "allow"}
    type: str
    title: str
    rating_key: int | None = None
    show: str | None = None
    season: str | None = None
    episode_number: int | None = None
    season_number: int | None = None
    year: str | None = None
    viewed_at: str | None = None


class UserWatchHistoryResponse(BaseModel):
    """Response from user_get_watch_history tool."""

    model_config = {"extra": "allow"}
    username: str
    count: int
    requested_limit: int
    content_type: str | None = None
    items: list[dict[str, str | int | None] | WatchHistoryItem]
    message: str | None = None


class UserStatisticsResponse(BaseModel):
    """Response from user_get_statistics tool."""

    model_config = {"extra": "allow"}
    time_period: str
    user_filter: str | None = None
    total_users: int
    stats_generated_at: str
    users: list[dict[str, str | int | dict[str, dict[str, int | str]]]]


# ============================================================================
# MEDIA, SERVER, SESSIONS, USER, PLAYLIST MODELS
# ============================================================================


# Generic models that can be reused across modules
class ListResponse(BaseModel):
    """Generic list response."""

    status: str
    message: str | None = None
    count: int | None = None
    items: list[dict[str, Any]] | list[str]


class OperationResponse(BaseModel):
    """Generic operation response with flexible data."""

    status: str
    message: str
    data: dict[str, Any] | None = None


class InfoResponse(BaseModel):
    """Generic info response."""

    status: str
    info: dict[str, Any]


# These generic models can handle most tool responses
# Individual tools can use these or create more specific ones as needed
