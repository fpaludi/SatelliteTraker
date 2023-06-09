from datetime import datetime, timedelta

from browser import aio, window

from satellite_tracker_client.utils import (
    cesium_date_to_datetime,
    hex_to_cesium_color,
    iso_to_cesium_date,
    calculate_visible_radius,
)


jq = window.jQuery
cesium = window.Cesium


class MapUI:
    """
    All the logic that handles the map related part of the UI of SatelliteTracker.
    """

    def __init__(self, app):
        self.app = app
        self.viewer = None

        # chunking configs. More info at docs/prediction_chunks.rst
        # how often do we check if we need to refresh predictions?
        self.predictions_refresh_real_seconds = 5
        # how many real seconds do we want to get on each prediction?
        self.predictions_chunk_real_seconds = 30 * 60
        # how many real seconds before we run out of predictions should fire a new request for
        # predictions?
        self.predictions_too_low_threshold_real_seconds = 15 * 60

        # initialize the map module
        self.configure_cesium_map()

        self.paths_visible = True
        self.sensors_visible = True

        # references to the dom
        self.paths_visible_input = jq("#paths-visible-input")
        self.sensors_visible_input = jq("#sensors-visible-input")
        self.night_shadow_input = jq("#night-shadow-input")
        self.map_date_picker = jq("#map-date-picker")
        self.go_to_date_button = jq("#go-to-date")

        # assign event handlers
        self.go_to_date_button.on("click", self.on_go_to_date_click)
        self.paths_visible_input.on("change", self.on_paths_visible_change)
        self.sensors_visible_input.on("change", self.on_sensors_visible_change)
        self.night_shadow_input.on("change", self.on_night_shadow_change)
        self.on_night_shadow_change()

        # every some time, ensure we have paths for each satellite
        aio.run(self.ensure_enough_predictions())

    def configure_cesium_map(self):
        """
        Configure the cesium map.
        """
        cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJmYjdiY2YzZi1iN2YyLTQ0NjQtYTRkMC02YTRlMWJiMDM2NTQiLCJpZCI6MTMyMzU3LCJpYXQiOjE2ODA3NTA5NDJ9.LXtKwlRmR0429H2VCmKwvAfHCSobFcyH3v0XOVbVsmE"

        cesium_config = {
            "homeButton": False,
            "navigationInstructionsInitiallyVisible": False,
            "sceneMode": cesium.SceneMode.SCENE2D,
            "fullscreenButton": False,
            "shouldAnimate": True,
        }
        self.viewer = cesium.Viewer.new("main-map", cesium_config)

        # center on 0,0 with enough distance to see the whole planet
        center = cesium.Cartesian3.fromDegrees(0, 0)
        self.viewer.camera.setView({"destination": center})

        # remove fog and ground atmosphere on 3d globe
        self.viewer.scene.fog.enabled = False
        self.viewer.scene.globe.showGroundAtmosphere = False

        # self.viewer.clock.onTick.addEventListener(self.on_map_tick)

    def on_map_tick(self, clock):
        """
        The map clock moved one tick.
        """
        # TODO
        pass

    def on_go_to_date_click(self, e):
        """
        Go to the selected date.
        """
        self.viewer.clock.currentTime = iso_to_cesium_date(
            self.map_date_picker.val() + "Z"
        )

    def real_to_map_seconds(self, real_seconds):
        """
        Convert real seconds to map seconds, because the map can be moving at a different speed.
        """
        clock = self.viewer.clock
        return clock.clockStep * clock.multiplier * real_seconds

    def on_dashboard_changed(self):
        """
        Called when the current dashboard suffers any change.
        """
        self.clear_map_data()
        # satellites don't need to be added here, because ensure_enough_predictions will take care
        # of automatically adding them in a few seconds
        if self.app.dashboard:
            self.add_locations(self.app.dashboard.locations)

    def clear_map_data(self):
        """
        Remove all data from the map.
        """
        self.viewer.entities.removeAll()

    def add_locations(self, locations):
        """
        Add new locations to the map.
        """
        for location in locations.values():
            location_entity = {
                "id": "SatelliteTracker.Location:{}".format(location.id),
                "name": location.name,
                "description": "<!--HTML-->\r\n<p>{}</p>".format(location.description),
                "point": {
                    "show": True,
                    "pixelSize": location.style.point_size,
                    "color": hex_to_cesium_color(location.style.point_color),
                    "heightReference": cesium.HeightReference.CLAMP_TO_GROUND,
                },
                "position": cesium.Cartesian3.fromDegrees(
                    location.longitude, location.latitude
                ),
            }

            self.viewer.entities.add(location_entity)

    async def ensure_enough_predictions(self):
        """
        Ensure the map has enough info to display paths for shown satellites.
        """
        sleep_seconds = self.predictions_refresh_real_seconds

        while True:
            await aio.sleep(sleep_seconds)
            print("Checking satellite paths for required predictions...")

            if not self.app.dashboard:
                print("Warning, no dashboard")
                continue

            map_now = cesium_date_to_datetime(self.viewer.clock.currentTime)

            # we should ensure we have predictions enough to cover the time between the current
            # date and map_now + self.predictions_too_low_threshold_real_seconds
            map_seconds_until_end = self.real_to_map_seconds(
                self.predictions_too_low_threshold_real_seconds
            )
            ensure_predictions_until = map_now + timedelta(
                seconds=map_seconds_until_end
            )
            map_seconds_arround = self.real_to_map_seconds(
                self.predictions_chunk_real_seconds
            )
            start_date = map_now - timedelta(seconds=map_seconds_arround)
            end_date = map_now + timedelta(seconds=map_seconds_arround)

            # if we have less than X real seconds of predictions left, then ask for Y predicted
            # seconds (more info at docs/prediction_chunks.rst)
            for satellite in self.app.dashboard.satellites.values():
                try:
                    if not satellite.path_covers(map_now, ensure_predictions_until):
                        # ask for the predictions
                        await satellite.get_path(
                            start_date,
                            end_date,
                            self.predictions_refresh_real_seconds,  # used as timeout
                            self.update_satellite_in_map,
                        )
                except Exception as err:
                    print(
                        "Error checking or getting path for satellite", satellite.name
                    )
                    print(err)

    def get_or_create_satellite_entity(self, satellite):
        """
        Build a cesium entity to display the satellite and its path in the map, or return an
        existing one if it's already there.
        """
        satellite_map_id = "SatelliteTracker.Satellite:{}".format(satellite.id)
        satellite_entity = self.viewer.entities.getById(satellite_map_id)

        if not satellite_entity:
            satellite_entity = self.viewer.entities.add(
                {
                    "id": satellite_map_id,
                    "availability": cesium.TimeIntervalCollection.new(),
                }
            )

        return satellite_entity

    def get_or_create_satellite_sensor_entity(self, satellite):
        """
        Build a cesium entity to display the satellite sensor in the map, or return an
        existing one if it's already there.
        """
        sensor_map_id = "SatelliteTracker.SatelliteSensor:{}".format(satellite.id)
        sensor_entity = self.viewer.entities.getById(sensor_map_id)

        if not sensor_entity:
            sensor_entity = self.viewer.entities.add(
                {
                    "id": sensor_map_id,
                    "availability": cesium.TimeIntervalCollection.new(),
                }
            )
        return sensor_entity

    def update_satellite_in_map(self, satellite):
        """
        Update the display data for a satellite shown in the map, based on its path predictions
        this will even add the satellite for the map if it wasn't already there.
        """
        satellite_entity = self.get_or_create_satellite_entity(satellite)
        sensor_entity = self.get_or_create_satellite_sensor_entity(satellite)

        # general satellite data
        satellite_entity.name = satellite.name
        satellite_entity.description = "<!--HTML-->\r\n<p>{}</p>".format(
            satellite.description
        )

        # show satellite in this specific interval
        # (we only trust the latest predictions, stuff like new tles could invalidate previous
        # ones)
        availability_interval = cesium.TimeInterval.new(
            {
                "start": iso_to_cesium_date(satellite.path_start_date.isoformat()),
                "stop": iso_to_cesium_date(satellite.path_end_date.isoformat()),
            }
        )
        satellite_entity.availability.removeAll()
        satellite_entity.availability.addInterval(availability_interval)
        sensor_entity.availability.removeAll()
        sensor_entity.availability.addInterval(availability_interval)

        # a point in the satellite position, that moves over time
        satellite_entity.point = cesium.PointGraphics.new(
            {
                "show": True,
                "pixelSize": satellite.style.point_size,
                "color": hex_to_cesium_color(satellite.style.point_color),
            }
        )

        # a circle in the satellite position, but on the ground, that moves over time and changes
        # size representing the area visible to the satellite
        sensor_ellipse_config = {
            "outline": True,
            "outlineColor": hex_to_cesium_color(satellite.style.sensor_color),
            "outlineWidth": satellite.style.sensor_line_width,
            "fill": satellite.style.sensor_fill,
        }
        if satellite.style.sensor_fill:
            sensor_ellipse_config["material"] = hex_to_cesium_color(
                satellite.style.sensor_color
            ).withAlpha(satellite.style.sensor_fill_alpha)
        sensor_entity.ellipse = cesium.EllipseGraphics.new(sensor_ellipse_config)

        # satellite positions over time
        position_property = cesium.SampledPositionProperty.new()
        sensor_radius_property = cesium.SampledProperty.new(window.Number)
        for path_position in satellite.path_positions:
            position_property.addSample(
                path_position.cesium_date, path_position.cesium_position
            )

            sensor_radius_property.addSample(
                path_position.cesium_date,
                calculate_visible_radius(path_position.altitude),
            )

        # set the properties that change through time
        satellite_entity.position = position_property
        sensor_entity.position = position_property
        sensor_entity.ellipse.semiMinorAxis = sensor_radius_property
        sensor_entity.ellipse.semiMajorAxis = sensor_radius_property

        sensor_entity.show = self.sensors_visible

        # path predicted behind and ahead the satellite
        satellite_entity.path = cesium.PathGraphics.new(
            {
                "show": self.paths_visible,
                "width": satellite.style.path_width,
                "material": hex_to_cesium_color(satellite.style.path_color),
                "resolution": 120,
                "leadTime": satellite.style.path_seconds_ahead,
                "trailTime": satellite.style.path_seconds_behind,
            }
        )

    def on_night_shadow_change(self, e=None):
        """
        On input change, decide wether to show or not the night shadow.
        """
        self.viewer.scene.globe.enableLighting = (
            self.night_shadow_input.prop("checked") is True
        )

    def on_paths_visible_change(self, e=None):
        """
        On input change, refresh the satellites so the paths get shown or hidden.
        """
        self.paths_visible = self.paths_visible_input.prop("checked") is True

        # refresh existing satellites in map
        for entity in self.viewer.entities.values:
            if entity.id.startswith("SatelliteTracker.Satellite:"):
                entity.path.show = self.paths_visible

    def on_sensors_visible_change(self, e=None):
        """
        On input change, refresh the satellites so the sensors get shown or hidden.
        """
        self.sensors_visible = self.sensors_visible_input.prop("checked") is True

        # refresh existing satellite sensors in map
        for entity in self.viewer.entities.values:
            if entity.id.startswith("SatelliteTracker.SatelliteSensor:"):
                entity.show = self.sensors_visible
