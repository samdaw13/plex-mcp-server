from typing import Any

from mcp.types import ToolAnnotations
from plexapi.exceptions import NotFound

from ..types.enums import ToolTag
from ..types.models import (
    CollectionAddResponse,
    CollectionCreateResponse,
    CollectionDeleteResponse,
    CollectionEditResponse,
    CollectionInfo,
    CollectionListResponse,
    CollectionRemoveResponse,
    ErrorResponse,
    LibraryCollections,
    PossibleMatch,
)
from . import connect_to_plex, mcp


@mcp.tool(
    name="collection_list",
    description="List all collections on the Plex server or in a specific library",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def collection_list(
    library_name: str | None = None,
) -> CollectionListResponse | ErrorResponse:
    """List all collections on the Plex server or in a specific library.

    Args:
        library_name: Optional name of the library to list collections from
    """
    try:
        plex = connect_to_plex()

        if library_name:
            try:
                library = plex.library.section(library_name)
                collections = library.collections()
                collections_data = [
                    CollectionInfo(
                        title=collection.title,
                        summary=collection.summary,
                        is_smart=collection.smart,
                        ID=collection.ratingKey,
                        items=collection.childCount,
                    )
                    for collection in collections
                ]

                return CollectionListResponse(collections=collections_data)
            except NotFound:
                return ErrorResponse(message=f"Library '{library_name}' not found")

        movie_libraries = []
        show_libraries = []

        for section in plex.library.sections():
            if section.type == "movie":
                movie_libraries.append(section)
            elif section.type == "show":
                show_libraries.append(section)

        libraries_collections = {}

        for library in movie_libraries:
            lib_collections = [
                CollectionInfo(
                    title=collection.title,
                    summary=collection.summary,
                    is_smart=collection.smart,
                    ID=collection.ratingKey,
                    items=collection.childCount,
                )
                for collection in library.collections()
            ]

            libraries_collections[library.title] = LibraryCollections(
                type="movie",
                collections_count=len(lib_collections),
                collections=lib_collections,
            )

        for library in show_libraries:
            lib_collections = [
                CollectionInfo(
                    title=collection.title,
                    summary=collection.summary,
                    is_smart=collection.smart,
                    ID=collection.ratingKey,
                    items=collection.childCount,
                )
                for collection in library.collections()
            ]

            libraries_collections[library.title] = LibraryCollections(
                type="show",
                collections_count=len(lib_collections),
                collections=lib_collections,
            )

        return CollectionListResponse(collections=libraries_collections)
    except Exception as e:
        return ErrorResponse(message=str(e))


@mcp.tool(
    name="collection_create",
    description="Create a new collection with specified items",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=False),
)
async def collection_create(
    collection_title: str,
    library_name: str,
    item_titles: list[str] | None = None,
    item_ids: list[int] | None = None,
) -> CollectionCreateResponse | ErrorResponse:
    """Create a new collection with specified items.

    Args:
        collection_title: Title for the new collection
        library_name: Name of the library to create the collection in
        item_titles: List of media titles to include in the collection (optional if item_ids is provided)
        item_ids: List of media IDs to include in the collection (optional if item_titles is provided)
    """
    try:
        plex = connect_to_plex()

        if (not item_titles or len(item_titles) == 0) and (not item_ids or len(item_ids) == 0):
            return ErrorResponse(message="Either item_titles or item_ids must be provided")

        try:
            library = plex.library.section(library_name)
        except NotFound:
            return ErrorResponse(message=f"Library '{library_name}' not found")

        try:
            existing_collection = next(
                (c for c in library.collections() if c.title.lower() == collection_title.lower()),
                None,
            )
            if existing_collection:
                return ErrorResponse(
                    message=f"Collection '{collection_title}' already exists in library '{library_name}'"
                )
        except Exception:
            pass

        items = []
        not_found: list[dict[str, Any] | str] = []

        if item_ids and len(item_ids) > 0:
            for item_id in item_ids:
                try:
                    item = plex.fetchItem(item_id)
                    if item:
                        items.append(item)
                    else:
                        not_found.append(str(item_id))
                except Exception:
                    not_found.append(str(item_id))

        if item_titles and len(item_titles) > 0:
            for title in item_titles:
                search_results = library.search(title=title)

                if search_results:
                    exact_matches = [
                        item for item in search_results if item.title.lower() == title.lower()
                    ]

                    if exact_matches:
                        items.append(exact_matches[0])
                    else:
                        possible_matches = []
                        for item in search_results:
                            possible_matches.append(
                                {
                                    "title": item.title,
                                    "id": item.ratingKey,
                                    "type": item.type,
                                    "year": item.year
                                    if hasattr(item, "year") and item.year
                                    else None,
                                }
                            )

                        not_found.append({"title": title, "possible_matches": possible_matches})
                else:
                    not_found.append(title)

        if not items and any(isinstance(item, dict) for item in not_found):
            possible_matches_list = []
            for item in not_found:
                if isinstance(item, dict) and "possible_matches" in item:
                    for match in item["possible_matches"]:
                        if match not in possible_matches_list:
                            possible_matches_list.append(match)

            return CollectionCreateResponse(
                status="error",
                possible_matches=[
                    PossibleMatch(title=m["title"], id=m["id"], type=m["type"], year=m.get("year"))
                    for m in possible_matches_list
                ],
            )

        if not items:
            return ErrorResponse(message="No matching media items found for the collection")

        collection = library.createCollection(title=collection_title, items=items)

        return CollectionCreateResponse(
            created=True,
            title=collection.title,
            id=collection.ratingKey,
            library=library_name,
            items_added=len(items),
            items_not_found=[item for item in not_found if not isinstance(item, dict)],
        )
    except Exception as e:
        return ErrorResponse(message=str(e))


@mcp.tool(
    name="collection_add_to",
    description="Add items to an existing collection",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=False),
)
async def collection_add_to(
    collection_title: str | None = None,
    collection_id: int | None = None,
    library_name: str | None = None,
    item_titles: list[str] | None = None,
    item_ids: list[int] | None = None,
) -> CollectionAddResponse | ErrorResponse:
    """Add items to an existing collection.

    Args:
        collection_title: Title of the collection to add to (optional if collection_id is provided)
        collection_id: ID of the collection to add to (optional if collection_title is provided)
        library_name: Name of the library containing the collection (required if using collection_title)
        item_titles: List of media titles to add to the collection (optional if item_ids is provided)
        item_ids: List of media IDs to add to the collection (optional if item_titles is provided)
    """
    try:
        plex = connect_to_plex()

        if not collection_id and not collection_title:
            return ErrorResponse(
                message="Either collection_id or collection_title must be provided"
            )

        if (not item_titles or len(item_titles) == 0) and (not item_ids or len(item_ids) == 0):
            return ErrorResponse(message="Either item_titles or item_ids must be provided")

        collection = None
        library = None

        if collection_id:
            try:
                try:
                    collection = plex.fetchItem(collection_id)
                except Exception:
                    collection = None
                    for section in plex.library.sections():
                        if section.type in ["movie", "show"]:
                            try:
                                for c in section.collections():
                                    if c.ratingKey == collection_id:
                                        collection = c
                                        library = section
                                        break
                                if collection:
                                    break
                            except Exception:
                                continue

                if not collection:
                    return ErrorResponse(message=f"Collection with ID '{collection_id}' not found")
            except Exception as e:
                return ErrorResponse(message=f"Error fetching collection by ID: {str(e)}")
        else:
            if not library_name:
                return ErrorResponse(
                    message="Library name is required when adding items by collection title"
                )

            try:
                library = plex.library.section(library_name)
            except NotFound:
                return ErrorResponse(message=f"Library '{library_name}' not found")

            matching_collections = [
                c
                for c in library.collections()
                if collection_title and c.title.lower() == collection_title.lower()
            ]

            if not matching_collections:
                return ErrorResponse(
                    message=f"Collection '{collection_title}' not found in library '{library_name}'"
                )

            if len(matching_collections) > 1:
                matches = [
                    {
                        "title": c.title,
                        "id": c.ratingKey,
                        "library": library_name,
                        "item_count": c.childCount if hasattr(c, "childCount") else len(c.items()),
                    }
                    for c in matching_collections
                ]

                return CollectionAddResponse(
                    status="multiple_matches", multiple_collections=matches
                )

            collection = matching_collections[0]

        items_to_add = []
        not_found: list[dict[str, Any] | str] = []
        already_in_collection = []
        current_items = collection.items()
        current_item_ids = [item.ratingKey for item in current_items]

        if item_ids and len(item_ids) > 0:
            for item_id in item_ids:
                try:
                    item = plex.fetchItem(item_id)
                    if item:
                        if item.ratingKey in current_item_ids:
                            already_in_collection.append(str(item_id))
                        else:
                            items_to_add.append(item)
                    else:
                        not_found.append(str(item_id))
                except Exception:
                    not_found.append(str(item_id))

        if item_titles and len(item_titles) > 0:
            if not library:
                for section in plex.library.sections():
                    if section.type == "movie" or section.type == "show":
                        try:
                            for c in section.collections():
                                if c.ratingKey == collection.ratingKey:
                                    library = section
                                    break
                            if library:
                                break
                        except Exception:
                            continue

                if not library:
                    return ErrorResponse(message="Could not determine which library to search in")

            for title in item_titles:
                search_results = library.search(title=title)

                if search_results:
                    exact_matches = [
                        item for item in search_results if item.title.lower() == title.lower()
                    ]

                    if exact_matches:
                        item = exact_matches[0]
                        if item.ratingKey in current_item_ids:
                            already_in_collection.append(title)
                        else:
                            items_to_add.append(item)
                    else:
                        possible_matches = []
                        for item in search_results:
                            possible_matches.append(
                                {
                                    "title": item.title,
                                    "id": item.ratingKey,
                                    "type": item.type,
                                    "year": item.year
                                    if hasattr(item, "year") and item.year
                                    else None,
                                }
                            )

                        not_found.append({"title": title, "possible_matches": possible_matches})
                else:
                    not_found.append(title)

        if not items_to_add and any(isinstance(item, dict) for item in not_found):
            possible_matches_list = []
            for item in not_found:
                if isinstance(item, dict) and "possible_matches" in item:
                    for match in item["possible_matches"]:
                        if match not in possible_matches_list:
                            possible_matches_list.append(match)

            return CollectionAddResponse(
                status="error",
                possible_matches=[
                    PossibleMatch(title=m["title"], id=m["id"], type=m["type"], year=m.get("year"))
                    for m in possible_matches_list
                ],
            )

        if not items_to_add and not already_in_collection:
            return ErrorResponse(message="No matching media items found to add to the collection")

        if items_to_add:
            collection.addItems(items_to_add)

        return CollectionAddResponse(
            added=True,
            title=collection.title,
            items_added=[item.title for item in items_to_add],
            items_already_in_collection=already_in_collection,
            items_not_found=[item for item in not_found if not isinstance(item, dict)],
            total_items=len(collection.items()),
        )
    except Exception as e:
        return ErrorResponse(message=str(e))


@mcp.tool(
    name="collection_remove_from",
    description="Remove items from an existing collection",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=False),
)
async def collection_remove_from(
    collection_title: str | None = None,
    collection_id: int | None = None,
    library_name: str | None = None,
    item_titles: list[str] | None = None,
) -> CollectionRemoveResponse | ErrorResponse:
    """Remove items from a collection.

    Args:
        collection_title: Title of the collection to remove from (optional if collection_id is provided)
        collection_id: ID of the collection to remove from (optional if collection_title is provided)
        library_name: Name of the library containing the collection (required if using collection_title)
        item_titles: List of media titles to remove from the collection
    """
    try:
        plex = connect_to_plex()

        if not collection_id and not collection_title:
            return ErrorResponse(
                message="Either collection_id or collection_title must be provided"
            )

        if not item_titles or len(item_titles) == 0:
            return ErrorResponse(message="At least one item title must be provided to remove")

        collection = None

        if collection_id:
            try:
                try:
                    collection = plex.fetchItem(collection_id)
                except Exception:
                    collection = None
                    for section in plex.library.sections():
                        if section.type in ["movie", "show"]:
                            try:
                                for c in section.collections():
                                    if c.ratingKey == collection_id:
                                        collection = c
                                        break
                                if collection:
                                    break
                            except Exception:
                                continue

                if not collection:
                    return ErrorResponse(message=f"Collection with ID '{collection_id}' not found")
            except Exception as e:
                return ErrorResponse(message=f"Error fetching collection by ID: {str(e)}")
        else:
            if not library_name:
                return ErrorResponse(
                    message="Library name is required when removing items by collection title"
                )

            try:
                library = plex.library.section(library_name)
            except NotFound:
                return ErrorResponse(message=f"Library '{library_name}' not found")

            matching_collections = [
                c
                for c in library.collections()
                if collection_title and c.title.lower() == collection_title.lower()
            ]

            if not matching_collections:
                return ErrorResponse(
                    message=f"Collection '{collection_title}' not found in library '{library_name}'"
                )

            if len(matching_collections) > 1:
                matches = [
                    {
                        "title": c.title,
                        "id": c.ratingKey,
                        "library": library_name,
                        "item_count": c.childCount if hasattr(c, "childCount") else len(c.items()),
                    }
                    for c in matching_collections
                ]

                return CollectionRemoveResponse(
                    status="multiple_matches", multiple_collections=matches
                )

            collection = matching_collections[0]

        collection_items = collection.items()
        items_to_remove = []
        not_found = []

        for title in item_titles:
            found = False
            for item in collection_items:
                if item.title.lower() == title.lower():
                    items_to_remove.append(item)
                    found = True
                    break
            if not found:
                not_found.append(title)

        if not items_to_remove:
            current_items = [
                {"title": item.title, "type": item.type, "id": item.ratingKey}
                for item in collection_items
            ]

            return CollectionRemoveResponse(
                status="error",
                collection_title=collection.title,
                collection_id=collection.ratingKey,
                current_items=current_items,
            )

        collection.removeItems(items_to_remove)

        return CollectionRemoveResponse(
            removed=True,
            title=collection.title,
            items_removed=[item.title for item in items_to_remove],
            items_not_found=not_found,
            remaining_items=len(collection.items()),
        )
    except Exception as e:
        return ErrorResponse(message=str(e))


@mcp.tool(
    name="collection_delete",
    description="Delete a collection from the Plex server",
    tags={ToolTag.DELETE.value},
    annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
)
async def collection_delete(
    collection_title: str | None = None,
    collection_id: int | None = None,
    library_name: str | None = None,
) -> CollectionDeleteResponse | ErrorResponse:
    """Delete a collection.

    Args:
        collection_title: Title of the collection to delete (optional if collection_id is provided)
        collection_id: ID of the collection to delete (optional if collection_title is provided)
        library_name: Name of the library containing the collection (required if using collection_title)
    """
    try:
        plex = connect_to_plex()

        if not collection_id and not collection_title:
            return ErrorResponse(
                message="Either collection_id or collection_title must be provided"
            )

        if collection_id:
            try:
                try:
                    collection = plex.fetchItem(collection_id)
                except Exception:
                    collection = None
                    for section in plex.library.sections():
                        if section.type in ["movie", "show"]:
                            try:
                                for c in section.collections():
                                    if c.ratingKey == collection_id:
                                        collection = c
                                        break
                                if collection:
                                    break
                            except Exception:
                                continue

                if not collection:
                    return ErrorResponse(message=f"Collection with ID '{collection_id}' not found")

                collection_title_to_return = collection.title
                collection.delete()

                return CollectionDeleteResponse(deleted=True, title=collection_title_to_return)
            except Exception as e:
                return ErrorResponse(message=f"Error fetching collection by ID: {str(e)}")

        if not library_name:
            return ErrorResponse(
                message="Library name is required when deleting by collection title"
            )

        try:
            library = plex.library.section(library_name)
        except NotFound:
            return ErrorResponse(message=f"Library '{library_name}' not found")

        matching_collections = [
            c
            for c in library.collections()
            if collection_title and c.title.lower() == collection_title.lower()
        ]

        if not matching_collections:
            return ErrorResponse(
                message=f"Collection '{collection_title}' not found in library '{library_name}'"
            )

        if len(matching_collections) > 1:
            matches = [
                {
                    "title": c.title,
                    "id": c.ratingKey,
                    "library": library_name,
                    "item_count": c.childCount if hasattr(c, "childCount") else len(c.items()),
                }
                for c in matching_collections
            ]

            return CollectionDeleteResponse(status="multiple_matches", multiple_collections=matches)

        collection = matching_collections[0]
        collection_title_to_return = collection.title
        collection.delete()

        return CollectionDeleteResponse(deleted=True, title=collection_title_to_return)
    except Exception as e:
        return ErrorResponse(message=str(e))


@mcp.tool(
    name="collection_edit",
    description="Edit collection metadata (title, summary, sorting)",
    tags={ToolTag.WRITE.value},
    annotations=ToolAnnotations(idempotentHint=True),
)
async def collection_edit(
    collection_title: str | None = None,
    collection_id: int | None = None,
    library_name: str | None = None,
    new_title: str | None = None,
    new_sort_title: str | None = None,
    new_summary: str | None = None,
    new_content_rating: str | None = None,
    new_labels: list[str] | None = None,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    poster_path: str | None = None,
    poster_url: str | None = None,
    background_path: str | None = None,
    background_url: str | None = None,
    new_advanced_settings: dict[str, Any] | None = None,
) -> CollectionEditResponse | ErrorResponse:
    """Comprehensively edit a collection's attributes.

    Args:
        collection_title: Title of the collection to edit (optional if collection_id is provided)
        collection_id: ID of the collection to edit (optional if collection_title is provided)
        library_name: Name of the library containing the collection (required if using collection_title)
        new_title: New title for the collection
        new_sort_title: New sort title for the collection
        new_summary: New summary/description for the collection
        new_content_rating: New content rating (e.g., PG-13, R, etc.)
        new_labels: Set completely new labels (replaces existing)
        add_labels: Labels to add to existing ones
        remove_labels: Labels to remove from existing ones
        poster_path: Path to a new poster image file
        poster_url: URL to a new poster image
        background_path: Path to a new background/art image file
        background_url: URL to a new background/art image
        new_advanced_settings: Dictionary of advanced settings to apply
    """
    try:
        plex = connect_to_plex()

        if not collection_id and not collection_title:
            return ErrorResponse(
                message="Either collection_id or collection_title must be provided"
            )

        collection = None

        if collection_id:
            try:
                try:
                    collection = plex.fetchItem(collection_id)
                except Exception:
                    collection = None
                    for section in plex.library.sections():
                        if section.type in ["movie", "show"]:
                            try:
                                for c in section.collections():
                                    if c.ratingKey == collection_id:
                                        collection = c
                                        break
                                if collection:
                                    break
                            except Exception:
                                continue

                if not collection:
                    return ErrorResponse(message=f"Collection with ID '{collection_id}' not found")
            except Exception as e:
                return ErrorResponse(message=f"Error fetching collection by ID: {str(e)}")
        else:
            if not library_name:
                return ErrorResponse(
                    message="Library name is required when editing by collection title"
                )

            try:
                library = plex.library.section(library_name)
            except NotFound:
                return ErrorResponse(message=f"Library '{library_name}' not found")

            matching_collections = [
                c
                for c in library.collections()
                if collection_title and c.title.lower() == collection_title.lower()
            ]

            if not matching_collections:
                return ErrorResponse(
                    message=f"Collection '{collection_title}' not found in library '{library_name}'"
                )

            if len(matching_collections) > 1:
                matches = [
                    {
                        "title": c.title,
                        "id": c.ratingKey,
                        "library": library_name,
                        "item_count": c.childCount if hasattr(c, "childCount") else len(c.items()),
                    }
                    for c in matching_collections
                ]

                return CollectionEditResponse(
                    status="multiple_matches", multiple_collections=matches
                )

            collection = matching_collections[0]

        changes = []
        edit_params = {}

        if new_title is not None and new_title != collection.title:
            edit_params["title"] = new_title
            changes.append(f"title to '{new_title}'")

        if new_sort_title is not None:
            current_sort = getattr(collection, "titleSort", "")
            if new_sort_title != current_sort:
                edit_params["titleSort"] = new_sort_title
                changes.append(f"sort title to '{new_sort_title}'")

        if new_summary is not None:
            current_summary = getattr(collection, "summary", "")
            if new_summary != current_summary:
                edit_params["summary"] = new_summary
                changes.append("summary")

        if new_content_rating is not None:
            current_rating = getattr(collection, "contentRating", "")
            if new_content_rating != current_rating:
                edit_params["contentRating"] = new_content_rating
                changes.append(f"content rating to '{new_content_rating}'")

        if edit_params:
            collection.edit(**edit_params)

        current_labels = getattr(collection, "labels", [])

        if new_labels is not None:
            collection.removeLabel(current_labels)
            if new_labels:
                collection.addLabel(new_labels)
            changes.append("labels completely replaced")
        else:
            if add_labels:
                for label in add_labels:
                    if label not in current_labels:
                        collection.addLabel(label)
                changes.append(f"added labels: {', '.join(add_labels)}")

            if remove_labels:
                for label in remove_labels:
                    if label in current_labels:
                        collection.removeLabel(label)
                changes.append(f"removed labels: {', '.join(remove_labels)}")

        if poster_path:
            collection.uploadPoster(filepath=poster_path)
            changes.append("poster (from file)")
        elif poster_url:
            collection.uploadPoster(url=poster_url)
            changes.append("poster (from URL)")

        if background_path:
            collection.uploadArt(filepath=background_path)
            changes.append("background art (from file)")
        elif background_url:
            collection.uploadArt(url=background_url)
            changes.append("background art (from URL)")

        if new_advanced_settings:
            for key, value in new_advanced_settings.items():
                try:
                    setattr(collection, key, value)
                    changes.append(f"advanced setting '{key}'")
                except Exception as setting_error:
                    return ErrorResponse(
                        message=f"Error setting advanced parameter '{key}': {str(setting_error)}"
                    )

        if not changes:
            return CollectionEditResponse(
                updated=False, message="No changes made to the collection"
            )

        collection_title_to_return = new_title if new_title else collection.title

        return CollectionEditResponse(
            updated=True, title=collection_title_to_return, changes=changes
        )
    except Exception as e:
        return ErrorResponse(message=str(e))
