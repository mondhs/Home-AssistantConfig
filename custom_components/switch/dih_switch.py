import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import SwitchDevice
from homeassistant.components.switch import (PLATFORM_SCHEMA, ENTITY_ID_FORMAT)
from homeassistant.const import (
    CONF_FRIENDLY_NAME, CONF_SWITCHES)
import homeassistant.helpers.config_validation as cv
import asyncio
import serial



_LOGGER = logging.getLogger(__name__)

CONF_SERIAL_PORT = 'serial_port'
CONF_BAUDRATE = 'baudrate'

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_FRIENDLY_NAME): cv.string
})

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SERIAL_PORT, default='/dev/ttyUSB0'): cv.string,
    vol.Optional(CONF_BAUDRATE, default=9600):cv.positive_int,
    vol.Required(CONF_SWITCHES): vol.Schema({cv.slug: SWITCH_SCHEMA}),
})

class DihDevice:
    def __init__(self, serial_port, baudrate):
        self.serial_port = serial_port
        self.baudrate = baudrate
    
    @asyncio.coroutine
    def async_turn_on(self, object_id):
        cmd_str = 'STATE?lamp1=on;\n'
        yield from self.async_execute(cmd_str)
        
    @asyncio.coroutine
    def async_turn_off(self, object_id):
        cmd_str = 'STATE?lamp1=off;\n'
        yield from self.async_execute(cmd_str)

        
    @asyncio.coroutine
    def async_execute(self, cmd_str):
        _LOGGER.error("[DihDevice] " + cmd_str)
        with serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=None, write_timeout=None) as ser:
            yield from asyncio.sleep(2)
            ser.write(cmd_str.encode())
            ser.flush()
            yield from asyncio.sleep(2)
            line=[]
            while (ser.in_waiting) or (len(line)==0):
                for c in ser.read():
                    line.append(chr(c))
            _LOGGER.error("[DihDevice] " +("".join(line)))

                
    def update(self):
        _LOGGER.error("[DihDevice]Update?")      
        
    def lights(self):
        return list(self)
      
    

@asyncio.coroutine
def async_setup_platform(hass, config, add_devices, discovery_info=None):

    devices = config.get(CONF_SWITCHES, {})
    switches = []
    serial_port = config.get(CONF_SERIAL_PORT)
    baudrate = config.get(CONF_BAUDRATE)
    dihDevice = DihDevice(serial_port, baudrate)
    
    for object_id, device_config in devices.items():
        _LOGGER.error("[DihDevice]setup " + object_id)
        switches.append(
            DihSwitch(
            object_id, 
            device_config.get(CONF_FRIENDLY_NAME, object_id),
            dihDevice))
    # Add devices
    add_devices(switches)



class DihSwitch(SwitchDevice):
    """Representation of an Dih Switch."""

    def __init__(self, object_id, friendly_name, dihDevice):
        """Initialize an DihSwitch."""
        self._dihDevice = dihDevice
        self._name = friendly_name
        self._lamp_id = object_id
        self._state = None
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        
    #@property
    #def unique_id(self):
    #    """Return the ID of this switch."""
    #    return "{}.{}".format(self.__class__, self.object_id)


    @property
    def should_poll(self):
        """No polling needed for a demo switch."""
        return False


    @property
    def name(self):
        """Return the display name of this switch."""
        return self._name


    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state


    @property
    def icon(self):
        return "mdi:flashlight"

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on.

        You can skip the brightness part if your switch does not support
        brightness control.
        """
        self._state = True
        yield from self._dihDevice.async_turn_on(self._lamp_id)
        self.async_schedule_update_ha_state()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        self._state = False
        yield from self._dihDevice.async_turn_off(self._lamp_id)
        self.async_schedule_update_ha_state()


