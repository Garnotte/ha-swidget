import asyncio
import json
import logging
import socket
from typing import Awaitable, Callable, Dict, Optional, Type, cast
from urllib.parse import urlparse

import ssdp

from .device import DeviceType, SwidgetDevice
from .swidgetdimmer import SwidgetDimmer
from .swidgetoutlet import SwidgetOutlet
from .swidgetswitch import SwidgetSwitch
from .swidgettimerswitch import SwidgetTimerSwitch
from .exceptions import SwidgetException

SWIDGET_HOST = "239.255.255.250:1900"
RESPONSE_SEC = 5
SWIDGET_ST = "urn:swidget:pico:1"
_LOGGER = logging.getLogger(__name__)
devices = dict()


class SwidgetDiscoveredDevice:
    def __init__(self, mac: str, host: str, firmware_version: str, friendly_name: str = "Swidget Discovered Device"):
        self.mac = mac
        self.host = host
        self.firmware_version = firmware_version
        self.friendly_name = friendly_name

class SwidgetProtocol(ssdp.SimpleServiceDiscoveryProtocol):
    """Protocol to handle responses and requests."""
    def response_received(self, response: ssdp.SSDPResponse, addr: tuple):
        "Handle an incoming response."
        headers = {h[0]: h[1] for h in response.headers}
        mac_address = headers["USN"].split("-")[-1]
        ip_address = urlparse(headers["LOCATION"]).hostname
        if headers["ST"] == SWIDGET_ST:
            _LOGGER.debug(headers["SERVER"])
            device_type = headers["SERVER"].split(" ")[1].split("+")[0]
            insert_type = headers["SERVER"].split(" ")[1].split("+")[1].split("/")[0]
            firmware_version = headers["SERVER"].split("/")[2].strip('"')
            friendly_name_a = headers["SERVER"].split("/")[0]
            friendly_name_b = headers["SERVER"].split(" ")[1].split("+")[0]
            friendly_name = friendly_name_a + ' ' + friendly_name_b

            devices[mac_address] = SwidgetDiscoveredDevice(mac_address, ip_address, firmware_version, friendly_name)

async def discover_devices():
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        SwidgetProtocol, family=socket.AF_INET
    )

    # Send out an M-SEARCH request, requesting Swidget service types.
    search_request = ssdp.SSDPRequest(
        "M-SEARCH",
        headers={
            "HOST": SWIDGET_HOST,
            "MAN": '"ssdp:discover"',
            "MX": RESPONSE_SEC,
            "ST": SWIDGET_ST,
        },
    )
    search_request.sendto(transport, (SwidgetProtocol.MULTICAST_ADDRESS, 1900))
    await asyncio.sleep(RESPONSE_SEC)
    _LOGGER.debug(f"Found the following Swidget devices from SSDP discovery: {devices}")
    return devices

def _get_device_class(device_type: str) -> Type[SwidgetDevice]:
    """Find SmartDevice subclass for device described by passed data."""
    if device_type == "outlet" or device_type == "outlet_20a":
        return SwidgetOutlet
    elif device_type == "switch":
        return SwidgetSwitch
    elif device_type == "dimmer":
        return SwidgetDimmer
    elif device_type == "pana_switch":
        return SwidgetTimerSwitch
    elif device_type == "relay_switch":
        return SwidgetSwitch
    raise SwidgetException("Unknown device type: %s" % device_type)


async def discover_single(host: str, password: str, ssl: bool) -> SwidgetDevice:
    """Discover a single device by the given IP address.

    :param host: Hostname of device to query
    :rtype: SwidgetDevice
    :return: Object for querying/controlling found device.
    """
    swidget_device = SwidgetDevice(host, password, ssl)
    await swidget_device.get_summary()
    device_type = swidget_device.device_type
    device_class = _get_device_class(device_type)
    dev = device_class(host, password, False)
    await dev.update()
    return dev
