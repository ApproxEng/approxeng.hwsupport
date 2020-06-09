# -*- coding: future_fstrings -*-

import logging

LOGGER = logging.getLogger(name='approxeng.hwsupport.adcs')
ADCS = 'adcs'


class ADC:
    """
    Holds configuration for a single ADC channel, you won't use this class directly.
    """

    def __init__(self, adc, divisor, board):
        self.adc = adc
        self.divisor = divisor
        self.board = board

    def get_divisor(self, _):
        return self.divisor

    def set_divisor(self, _, value):
        self.divisor = value

    def get_value(self, _):
        return self.board.read_adc(adc=self.adc)


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
            raw_value = self._read_adc(adc=adc, **kwargs)
            return round(float(raw_value) / config.divisor, ndigits=digits)
        else:
            raise ValueError(f'board has no adc functions, unable to read adc{adc}')
