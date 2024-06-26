from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID

from qmixsdk.qmixcontroller import ControllerChannel
from sila2.server import SilaServer

from .feature_implementations.controlloopservice_impl import ControlLoopServiceImpl
from .generated.controlloopservice import ControlLoopServiceFeature


class Server(SilaServer):
    def __init__(
        self,
        controller_channels: List[ControllerChannel],
        server_name: str = "",
        server_type: str = "",
        server_description: str = "",
        server_version: str = "",
        server_vendor_url: str = "",
        server_uuid: Optional[Union[str, UUID]] = None,
    ):
        from ... import __version__

        super().__init__(
            server_name=server_name or "Control Loop Service",
            server_type=server_type or "TestServer",
            server_description=server_description or "The SiLA 2 driver for CETONI reaction modules",
            server_version=server_version or __version__,
            server_vendor_url=server_vendor_url or "https://www.cetoni.com",
            server_uuid=server_uuid,
        )

        self.controlloopservice = ControlLoopServiceImpl(self, controller_channels)

        self.set_feature_implementation(ControlLoopServiceFeature, self.controlloopservice)
