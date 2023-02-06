from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Dict, Generic, List, Optional, TypeVar, Union, overload

from qmixsdk import qmixcontroller

from sila_cetoni.application.device import CetoniDevice, Device

from .sila.controllers_service.server import Server

if TYPE_CHECKING:
    from sila_cetoni.application.application_configuration import ApplicationConfiguration
    from sila_cetoni.application.cetoni_device_configuration import CetoniDeviceConfiguration

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


# currently only a placeholder until we support controller devices from other manufacturers, as well
class ControllerDevice(Device, Generic[_T]):
    """
    Simple class to represent a controller device with (possibly) multiple controller channels

    Template Parameters
    -------------------
    _T: type
        The type of the controller channels (e.g. `qmixcontroller.ControllerChannels`)
    """

    _controller_channels: List[_T]

    def __init__(self, name: str, manufacturer: str, simulated: bool, *, device_type="controllers", **kwargs) -> None:
        # `**kwargs` for additional arguments that are not used and that might come from `ThirdPartyDevice.__init__` as
        # the result of `ThirdPartyControllerDevice.__init__`
        super().__init__(
            name=name, device_type=device_type or "controllers", manufacturer=manufacturer, simulated=simulated
        )
        self._controller_channels = []

    @property
    def controller_channels(self) -> List[_T]:
        return self._controller_channels

    @controller_channels.setter
    def controller_channels(self, controller_channels: List[_T]):
        self._controller_channels = controller_channels


# `CetoniControllerDevice` *is* a `ControllerDevice`, as well, via duck typing
class CetoniControllerDevice(CetoniDevice[qmixcontroller.ControllerChannel]):
    """
    Simple class to represent a controller device that has an arbitrary number of controller channels
    (inherited from the `CetoniDevice` class)
    """

    def __init__(self, name: str) -> None:
        super().__init__(name, "controllers")


def parse_devices(json_devices: Optional[Dict[str, Dict]]) -> List[CetoniControllerDevice]:
    """
    Parses the given JSON configuration `json_devices` and creates the necessary `CetoniControllerDevice`s

    Parameters
    ----------
    json_devices: Dict[str, Dict] (optional)
        The `"devices"` section of the JSON configuration file as a dictionary (key is the device name, the value is a
        dictionary with the configuration parameters for the device, i.e. `"type"`, `"manufacturer"`, ...)

    Returns
    -------
    List[CetoniControllerDevice]
        A list with all `CetoniControllerDevice`s as defined in the JSON config
    """
    # CETONI devices are not defined directly in the JSON config
    return []


@overload
def create_devices(config: ApplicationConfiguration, scan: bool = False) -> None:
    """
    Looks up all controller devices from the current configuration and tries to auto-detect more devices if `scan` is
    `True`

    Parameters
    ----------
    config: ApplicationConfiguration
        The application configuration containing all devices for which SiLA Server and thus device driver instances
        shall be created
    scan: bool (default: False)
        Whether to scan for more devices than the ones defined in `config`
    """
    ...


@overload
def create_devices(config: CetoniDeviceConfiguration) -> List[CetoniControllerDevice]:
    """
    Looks up all CETONI devices from the given configuration `config` and creates the necessary `CetoniControllerDevice`s for them

    Parameters
    ----------
    config: CetoniDeviceConfiguration
        The CETONI device configuration

    Returns
    -------
    List[CetoniControllerDevice]
        A list with all `CetoniControllerDevice`s from the device configuration
    """
    ...


def create_devices(config: Union[ApplicationConfiguration, CetoniDeviceConfiguration], *args, **kwargs):
    from sila_cetoni.application.application_configuration import ApplicationConfiguration
    from sila_cetoni.application.cetoni_device_configuration import CetoniDeviceConfiguration

    if isinstance(config, ApplicationConfiguration):
        logger.info(
            f"Package {__name__!r} currently only supports CETONI devices. Parameter 'config' must be of type "
            f"'CetoniDeviceConfiguration'!"
        )
        return
    if isinstance(config, CetoniDeviceConfiguration):
        return create_devices_cetoni(config)
    raise ValueError(
        f"Parameter 'config' must be of type 'ApplicationConfiguration' or 'CetoniDeviceConfiguration', not"
        f"{type(config)!r}!"
    )


def create_devices_cetoni(config: CetoniDeviceConfiguration) -> List[CetoniControllerDevice]:
    """
    Implementation of `create_devices` for devices from the CETONI device config

    See `create_devices` for an explanation of the parameters and return value
    """

    channel_count = qmixcontroller.ControllerChannel.get_no_of_channels()
    logger.debug(f"Number of controller channels: {channel_count}")

    channels: List[qmixcontroller.ControllerChannel] = []
    for i in range(channel_count):
        channel = qmixcontroller.ControllerChannel()
        channel.lookup_channel_by_index(i)
        logger.debug(f"Found controller channel {i} named {channel.get_name()}")
        channels.append(channel)

    devices: List[CetoniControllerDevice] = []
    for channel in channels:
        channel_name = channel.get_name()
        # Using `config.devices` here and operating directly on these devices is somewhat contradictory to the
        # decoupling between sila_cetoni.application and the add-on packages that this method should achieve. However,
        # this seems to be the only viable way for now.
        for device in devices + config.devices:
            if device.name.rsplit("_Pump", 1)[0] in channel_name:
                logger.debug(f"Channel {channel_name} belongs to device {device}")
                device.controller_channels.append(channel)
                break
        else:
            device_name = re.match(
                r".*(?=(_Temperature)|(_ReactionLoop)|(_ReactorZone)|(_Ctrl)\d?$)", channel_name
            ).group()
            logger.debug(f"Standalone controller device {device_name}")
            device = CetoniControllerDevice(device_name)
            logger.debug(f"Channel {channel_name} belongs to device {device}")
            device.controller_channels.append(channel)
            devices.append(device)

    return devices


def create_server(device: ControllerDevice, **server_args) -> Server:
    """
    Creates the SiLA Server for the given `device`

    Parameters
    ----------
    device: Device
        The device for which to create a SiLA Server
    **server_args
        Additional arguments like server name, server UUID to pass to the server's `__init__` function
    """
    logger.info(f"Creating server for {device}")
    return Server(controller_channels=device.controller_channels, **server_args)
