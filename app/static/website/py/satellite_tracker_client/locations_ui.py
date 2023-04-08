from browser import window


jq = window.jQuery


class LocationsUI:
    """
    All the logic that handles the locations related part of the UI of SatelliteTracker.
    """

    def __init__(self, app):
        self.app = app
