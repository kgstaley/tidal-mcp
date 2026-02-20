"""Mixes endpoint - TIDAL API wrapper for mix operations"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_client.session import TidalSession


class MixesEndpoint:
    """Handle all mix-related API operations"""

    def __init__(self, session: "TidalSession"):
        """Initialize endpoint with session.

        Args:
            session: TidalSession instance for making API requests
        """
        self.session = session

    def get_user_mixes(self) -> list[dict]:
        """Fetch the authenticated user's mixes.

        Calls GET pages/my_collection_my_mixes and walks the nested
        rows -> modules -> pagedList.items pages structure to collect
        all mix items.

        Returns:
            List of raw mix dicts from the TIDAL API, each containing
            id, title, subTitle, shortSubtitle, mixType, and images fields.
        """
        result = self.session.request("GET", "pages/my_collection_my_mixes")
        mixes = []
        for row in result.get("rows", []):
            for module in row.get("modules", []):
                paged_list = module.get("pagedList", {}) or {}
                for item in paged_list.get("items", []):
                    if "id" in item:
                        mixes.append(item)
        return mixes

    def get_mix_tracks(self, mix_id: str) -> list[dict]:
        """Fetch the tracks for a specific mix.

        Calls GET pages/mix?mixId={mix_id}&deviceType=BROWSER and extracts
        tracks from the second row onward (the first row contains mix metadata).

        Args:
            mix_id: TIDAL mix identifier

        Returns:
            List of raw track dicts from the TIDAL API.

        Raises:
            NotFoundError: If the mix does not exist (404 response).
        """
        result = self.session.request(
            "GET",
            "pages/mix",
            params={"mixId": mix_id, "deviceType": "BROWSER"},
        )
        rows = result.get("rows", [])
        # First row is mix metadata; subsequent rows contain the track list
        for row in rows[1:]:
            for module in row.get("modules", []):
                paged_list = module.get("pagedList", {}) or {}
                items = paged_list.get("items", [])
                if items:
                    return items
        return []
