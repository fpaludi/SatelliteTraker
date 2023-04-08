from browser import window


jq = window.jQuery


class DashboardsUI:
    """
    All the logic that handles the dashboards related part of the UI of SatelliteTracker.
    """
    def __init__(self, app):
        self.app = app
