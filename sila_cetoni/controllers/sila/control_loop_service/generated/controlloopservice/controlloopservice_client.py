# Generated by sila2.code_generator; sila2.__version__: 0.8.0
# -----
# This class does not do anything useful at runtime. Its only purpose is to provide type annotations.
# Since sphinx does not support .pyi files (yet?), so this is a .py file.
# -----

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from typing import Iterable, Optional

    from controlloopservice_types import RunControlLoop_Responses, StopControlLoop_Responses, WriteSetPoint_Responses
    from sila2.client import (
        ClientMetadata,
        ClientMetadataInstance,
        ClientObservableCommandInstance,
        ClientObservableProperty,
        ClientUnobservableProperty,
    )


class ControlLoopServiceClient:
    """
    Allows to control a Qmix Device with a Control Loop
    """

    NumberOfChannels: ClientUnobservableProperty[int]
    """
    The number of controller channels.
    """

    ControllerValue: ClientObservableProperty[float]
    """
    The actual value from the Device
    """

    SetPointValue: ClientObservableProperty[float]
    """
    The current SetPoint value of the Device
    """

    ChannelIndex: ClientMetadata[int]
    """
    The index of the channel that should be used. This value is 0-indexed, i.e. the first channel has index 0, the second one index 1 and so on.
    """

    def WriteSetPoint(
        self, SetPointValue: float, *, metadata: Optional[Iterable[ClientMetadataInstance]] = None
    ) -> WriteSetPoint_Responses:
        """
        Write a Set Point value to the Controller Device
        """
        ...

    def StopControlLoop(
        self, *, metadata: Optional[Iterable[ClientMetadataInstance]] = None
    ) -> StopControlLoop_Responses:
        """
        Stops the Control Loop (has no effect, if no Loop is currently running)
        """
        ...

    def RunControlLoop(
        self, *, metadata: Optional[Iterable[ClientMetadataInstance]] = None
    ) -> ClientObservableCommandInstance[RunControlLoop_Responses]:
        """
        Run the Control Loop
        """
        ...
