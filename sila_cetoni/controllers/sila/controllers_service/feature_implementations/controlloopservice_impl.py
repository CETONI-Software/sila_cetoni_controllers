# Generated by sila2.code_generator; sila2.__version__: 0.8.0
from __future__ import annotations

import logging
import math
import time
from concurrent.futures import Executor
from queue import Queue
from threading import Event
from typing import Any, Dict, List, Optional, Union, cast

from qmixsdk.qmixcontroller import ControllerChannel
from sila2.framework import Command, Feature, FullyQualifiedIdentifier, Metadata, Property
from sila2.server import MetadataDict, ObservableCommandInstance, SilaServer

from ..generated.controlloopservice import (
    ControlLoopServiceBase,
    ControlLoopServiceFeature,
    InvalidChannelIndex,
    RunControlLoop_Responses,
    StopControlLoop_Responses,
    WriteSetPoint_Responses,
)

logger = logging.getLogger(__name__)


class ControlLoopServiceImpl(ControlLoopServiceBase):
    __controller_channels: List[ControllerChannel]
    __channel_index_identifier: Metadata[int]
    __set_point_queues: List[Queue[float]]  # same number of items and order as `__controller_channels`
    __controller_value_queues: List[Queue[float]]  # same number of items and order as `__controller_channels`
    __stop_event: Event

    def __init__(self, server: SilaServer, controller_channels: List[ControllerChannel], executor: Executor):
        super().__init__(server)
        self.__controller_channels = controller_channels
        self.__channel_index_identifier = cast(Metadata, ControlLoopServiceFeature["ChannelIndex"])

        self.__stop_event = Event()

        self.__set_point_queues = []
        self.__controller_value_queues = []
        for i in range(len(self.__controller_channels)):
            self.__set_point_queues += [Queue()]
            self.__controller_value_queues += [Queue()]

            # initial values
            self.update_SetPointValue(
                self.__controller_channels[i].get_setpoint(),
                queue=self.__set_point_queues[i],
            )
            self.update_ControllerValue(
                self.__controller_channels[i].read_actual_value(),
                queue=self.__controller_value_queues[i],
            )

            executor.submit(self.__make_set_point_updater(i), self.__stop_event)
            executor.submit(self.__make_controller_value_updater(i), self.__stop_event)

    def __make_set_point_updater(self, i: int):
        def update_set_point(stop_event: Event):
            new_set_point = set_point = self.__controller_channels[i].get_setpoint()
            while not stop_event.is_set():
                new_set_point = self.__controller_channels[i].get_setpoint()
                if not math.isclose(new_set_point, set_point):
                    set_point = new_set_point
                    self.update_SetPointValue(set_point, queue=self.__set_point_queues[i])
                time.sleep(0.1)

        return update_set_point

    def __make_controller_value_updater(self, i: int):
        def update_set_point(stop_event: Event):
            new_controller_value = controller_value = self.__controller_channels[i].read_actual_value()
            while not stop_event.is_set():
                new_controller_value = self.__controller_channels[i].read_actual_value()
                if not math.isclose(new_controller_value, controller_value):
                    controller_value = new_controller_value
                    self.update_ControllerValue(controller_value, queue=self.__controller_value_queues[i])
                time.sleep(0.1)

        return update_set_point

    def get_NumberOfChannels(self, *, metadata: MetadataDict) -> int:
        return len(self.__controller_channels)

    def SetPointValue_on_subscription(self, *, metadata: MetadataDict) -> Optional[Queue[float]]:
        channel_index = metadata.get(self.__channel_index_identifier, 0)
        try:
            if channel_index < 0:
                raise IndexError
            return self.__set_point_queues[channel_index]
        except IndexError:
            raise InvalidChannelIndex(
                message=f"The sent channel index {channel_index} is invalid. The index must be between 0 and {len(self.__controller_channels) - 1}.",
            )

    def ControllerValue_on_subscription(self, *, metadata: MetadataDict) -> Optional[Queue[float]]:
        channel_index = metadata.get(self.__channel_index_identifier, 0)
        try:
            return self.__controller_value_queues[channel_index]
        except IndexError:
            raise InvalidChannelIndex(
                message=f"The sent channel index {channel_index} is invalid. The index must be between 0 and {len(self.__controller_channels) - 1}.",
            )

    def __controller_channel_for_index(self, channel_index: int) -> ControllerChannel:
        try:
            return self.__controller_channels[channel_index]
        except IndexError:
            raise InvalidChannelIndex(
                message=f"The sent channel index {channel_index} is invalid. The index must be between 0 and {len(self.__controller_channels) - 1}.",
            )

    def WriteSetPoint(self, SetPointValue: float, *, metadata: MetadataDict) -> WriteSetPoint_Responses:
        channel_identifier: int = metadata.get(self.__channel_index_identifier, 0)
        logger.debug(f"channel id: {channel_identifier}")
        self.__controller_channel_for_index(channel_identifier).write_setpoint(SetPointValue)
        return WriteSetPoint_Responses()

    def StopControlLoop(self, *, metadata: MetadataDict) -> StopControlLoop_Responses:
        channel_identifier: int = metadata.get(self.__channel_index_identifier, 0)
        logger.debug(f"channel id: {channel_identifier}")
        self.__controller_channel_for_index(channel_identifier).enable_control_loop(False)
        return StopControlLoop_Responses()

    def RunControlLoop(
        self,
        *,
        metadata: MetadataDict,
        instance: ObservableCommandInstance,
    ) -> RunControlLoop_Responses:
        channel_identifier: int = metadata.get(self.__channel_index_identifier, 0)
        logger.debug(f"channel id: {channel_identifier}")
        self.__controller_channel_for_index(channel_identifier).enable_control_loop(True)
        return RunControlLoop_Responses()

    def get_calls_affected_by_ChannelIndex(
        self,
    ) -> List[Union[Feature, Command, Property, FullyQualifiedIdentifier]]:
        if len(self.__controller_channels) == 1:
            return []
        else:
            return [
                cast(Command, ControlLoopServiceFeature["WriteSetPoint"]),
                cast(Command, ControlLoopServiceFeature["RunControlLoop"]),
                cast(Command, ControlLoopServiceFeature["StopControlLoop"]),
                cast(Command, ControlLoopServiceFeature["ControllerValue"]),
                cast(Command, ControlLoopServiceFeature["SetPointValue"]),
            ]

    def stop(self) -> None:
        super().stop()
        self.__stop_event.set()
