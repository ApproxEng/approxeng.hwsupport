# -*- coding: future_fstrings -*-

import logging
import time

LOGGER = logging.getLogger(name='approxeng.hwsupport.adcs')
ADCS = 'adcs'


class ADC:
    """
    Holds configuration for a single ADC channel, you won't use this class directly.
    """

    def __init__(self, adc, divisor, cache_time, board):
        self.adc = adc
        self.divisor = divisor
        self.cache_time = cache_time
        self.board = board
        self.last_reading_time = None
        self.last_reading_value = None

    @property
    def config(self):
        return {'divisor': self.divisor, 'cache_time': self.cache_time}

    @config.setter
    def config(self, d):
        if 'divisor' in d:
            self.set_divisor(None, d['divisor'])
        if 'cache_time' in d:
            self.set_cache_time(None, d['cache_time'])

    def get_divisor(self, _):
        return self.divisor

    def set_divisor(self, _, value):
        self.divisor = value

    def get_value(self, _):
        return self.board.read_adc(adc=self.adc)

    def get_cache_time(self, _):
        return self.cache_time

    def set_cache_time(self, _, value):
        if value is not None and isinstance(value, int):
            value = float(value)
        if value is None or not isinstance(value, float) or value < 0:
            raise ValueError(f'adc adc{self.adc}_cache_time must be a float >=0.0, value was {value}')
        self.cache_time = value


class ReadADCsMixin:
    """
    Mixed into the new class used for the augmented instance to provide the read_adc method
    """

    def read_adc(self, adc, digits=2, **kwargs):
        """
        Read an ADC value, applying the configured multiplier

        :param adc:
            The adc channel to read, must be a value in the array of adcs
        :param digits:
            Number of digits to round the result, defaults to 2
        :param kwargs:
            Any additional arguments to provide to the underlying _read_adc method
        :raises:
            ValueError if the supplied channel doesn't exist, or the board has no ADC functionality
        """
        if ADCS in self._config:
            LOGGER.debug(f'read adc{adc}')
            if adc not in self._config[ADCS]:
                raise ValueError(f'adc adc{adc} is not in {list(self._config[ADCS].keys())}')
            config = self._config[ADCS][adc]
            # Check for caching
            new_value = False
            if config.cache_time == 0:
                # Caching is disabled
                new_value = True
            else:
                # Caching is enabled, need the current time
                now = time.time()
                if config.last_reading_time is None or config.last_reading_time < (now - config.cache_time):
                    # Enabled, cached value out of date
                    new_value = True
                    config.last_reading_time = now
            if new_value:
                # Need a new value for the cache and to return
                raw_value = self._read_adc(adc=adc, **kwargs)
                adjusted_value = round(float(raw_value) / config.divisor, ndigits=digits)
                config.last_reading_value = adjusted_value
                return adjusted_value
            else:
                # Return cached value
                return config.last_reading_value
        else:
            raise ValueError(f'board has no adc functions, unable to read adc{adc}')
