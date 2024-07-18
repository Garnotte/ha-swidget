from .device import (
    DeviceType,
    SwidgetDevice
)

from .exceptions import SwidgetException

class SwidgetTimerSwitch(SwidgetDevice):

    def __init__(self, host,  secret_key: str, ssl: bool) -> None:
        super().__init__(host=host, secret_key=secret_key, ssl=ssl)
        self._device_type = DeviceType.TimerSwitch

    #async def current_consumption(self) -> float:
    #    """Get the current power consumption in watts."""
    #    return sum([await plug.current_consumption() for plug in self.children])

    @property  # type: ignore
    def is_on(self) -> bool:
        """Return whether device is on."""
        toggle_state = self.assemblies['host'].components["0"].functions['toggle']["state"]
        buttonLevel_state = self.assemblies['host'].components['0'].functions['timer']['buttonLevel']
        buttonTimer_state = self.assemblies['host'].components['0'].functions['timer']['buttonTimer']
        if buttonLevel_state != 0 and toggle_state == "on":
            return True
        else:
            return False
        
    @property
    def timer_duration(self) -> float:
        """Return current remaining time on timer.

        Will return a preset range between 0 - 1hr.
        """
        if not self.is_pana_switch:
            raise SwidgetException("Device is not a timer switch.")
        try:
            return self.assemblies['host'].components['0'].functions['timer']['buttonTimer']
        except:
            raise SwidgetException

    async def set_timer_duration(self, timer_duration):
        """Set the brightness of the device."""
        await self.send_command(
            assembly="host", component="0", function="timer", command={"duration": timer_duration}
        )

    @property  # type: ignore
    def is_pana_switch(self) -> bool:
        """Whether the switch supports timers."""
        return True

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes


    async def set_countdown_timer(self, minutes: int):
        """Set the countdown timer."""
        await self.send_command(
            assembly="host", component="0", function="timer", command={"duration": minutes}
        )

    async def activate_fan(self, duration: int):
        """Activate the fan for the specified duration."""
        await self.send_command(
            assembly="host", component="0", function="timer", command={"duration": duration // 60 }
        )

    async def turn_on(self):
        """Turn the device on."""
        await self.send_command(
            assembly="host", component="0", function="toggle", command={"state": "on"}
        )
    async def turn_off(self):
        """Turn the device off."""
        await self.send_command(
            assembly="host", component="0", function="toggle", command={"state": "off"}
        )

    @property  # type: ignore
    def usb_is_on(self) -> bool:
        """Return whether USB is on."""
        usb_state = self.assemblies['insert'].components["usb"].functions['toggle']["state"]
        if usb_state == "on":
            return True
        return False

    async def turn_on_usb_insert(self):
        """Turn the USB insert on."""
        await self.send_command(
            assembly="insert", component="usb", function="toggle", command={"state": "on"}
        )

    async def turn_off_usb_insert(self):
        """Turn the USB insert off."""
        await self.send_command(
            assembly="insert", component="usb", function="toggle", command={"state": "off"}
        )