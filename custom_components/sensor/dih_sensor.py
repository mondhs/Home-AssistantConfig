import logging
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA
from homeassistant.const import (TEMP_CELSIUS, CONF_SENSORS, ATTR_FRIENDLY_NAME)
import serial
import re
import json
import sys


import voluptuous as vol
import asyncio
import homeassistant.helpers.config_validation as cv

from datetime import timedelta


SENSOR_SCHEMA = vol.Schema({
    vol.Required(ATTR_FRIENDLY_NAME): cv.string,
    })
    
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: SENSOR_SCHEMA}),
})

_LOGGER = logging.getLogger(__name__)

@asyncio.coroutine
# pylint: disable=unused-argument
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the sensor platform."""
    sensors = []
    sensor_handler = yield from hass.async_add_job(DIhHandler)
    
    for device, device_config in config[CONF_SENSORS].items():
        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        
        
        
        sensors.append(DihSensor(
            hass,
            device,
            friendly_name,
            sensor_handler
            ))
    if not sensors:
        _LOGGER.error("No sensors added")
        return False

    async_add_devices(sensors)
    return True
    
    
class DIhHandler:
    """Implement Dih communication."""

    def __init__(self ):
        """Initialize the sensor handler."""
        self.messageMap = dict([("temp0",0), ("temp1",0),("temp2",0), ("temp9",0)])

    @asyncio.coroutine
    def async_update(self, device_id):
        if device_id != "temp0":
            return
        _LOGGER.info("+++DIhHandler update." + device_id )
        """Read raw data and calculate temperature and humidity."""
        with serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=None, write_timeout=None) as ser:
            yield from asyncio.sleep(2)
            ser.write(b'DATA?\n')
            ser.flush()
            yield from asyncio.sleep(2)
            line=[]
            while (ser.in_waiting) or (len(line)==0):
                for c in ser.read():
                    line.append(chr(c))
            msg = re.sub(r';temp.*$', "", "".join(line)).strip()
            #print(msg)
            _LOGGER.error("DIhHandler update." + msg )
            newMessageMap = dict(item.split("=") for item in msg.split('\r\n'))
            newMessageMap["temp9"]=float(newMessageMap["waterLevel"])/8
        _LOGGER.info("---DIhHandler update." + device_id + "; map: "+ str(newMessageMap))
        self.messageMap = newMessageMap
    
class DihSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, hass, device_id, friendly_name, sensor_handler):
        """Initialize the sensor."""
        self._state = None
        self.hass = hass
        self._name = friendly_name
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, device_id,
                                                  hass=hass)
        self._device_id=device_id
        self._sensor_handler = sensor_handler

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        if self._device_id == "temp9":
            return "%"
        """Return the unit of measurement."""
        return TEMP_CELSIUS
        
    @asyncio.coroutine
    def async_update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("+++async update. Device id: " + self._device_id)
        yield from self._sensor_handler.async_update(self._device_id)
        try:
            if self._device_id in self._sensor_handler.messageMap:
                self._state = self._sensor_handler.messageMap[self._device_id]
        except:
            e = sys.exc_info()[0]
            _LOGGER.error("async update. Error with Device id: " + self._device_id)
            _LOGGER.error(e)
        _LOGGER.info("---async update. Device id: " + self._device_id)

