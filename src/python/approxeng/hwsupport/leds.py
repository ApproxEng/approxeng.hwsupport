# -*- coding: future_fstrings -*-

import colorsys
import logging

from approxeng.hwsupport.css4_colours import CSS4_COLOURS

LOGGER = logging.getLogger(name='approxeng.hwsupport.leds')

LEDS = 'leds'


class LED:
    def __init__(self, led, board):
        self.led = led
        self.board = board
        self.brightness = 1.0
        self.hsv = (0, 0, 0)

    def set_colour(self, _, value):
        if isinstance(value, tuple):
            self.board.set_led_hsv(self.led, *value)
        elif value in CSS4_COLOURS:
            self.board.set_led_hsv(self.led, CSS4_COLOURS[value])
        else:
            LOGGER.warning(f'colour for led{self.led} is neither a triple or a colour name')

    def set_colour_rgb(self, _, value):
        if isinstance(value, tuple) and len(value) == 3:
            self.board.set_led_rgb(self.led, *value)

    def get_colour_rgb(self, _):
        return colorsys.hsv_to_rgb(*self.hsv)

    def get_colour(self, _):
        return self.hsv

    def set_brightness(self, _, value):
        self.board.set_led_brightness(self.led, value)

    def get_brightness(self, _):
        return self.brightness


class SetLEDsMixin:

    def _check_led_index(self, led):
        """
        Check that a servo is valid, raising ValueError if not and returning the config otherwise.
        """
        if LEDS not in self._config:
            raise ValueError(f'board has no LED functions, unable to control led{led}')
        if led not in self._config[LEDS]:
            raise ValueError(f'LED led{led} not in {list(self._config[LEDS].keys())}')
        return self._config[LEDS][led]

    def set_led_brightness(self, led, brightness):
        config = self._check_led_index(led)
        config.brightness = _check_positive(brightness)
        self._update_led(config)

    def set_led_hsv(self, led, h, s, v):
        config = self._check_led_index(led)
        try:
            h = float(h) % 1.0
            s = _check_positive(float(s))
            v = _check_positive(float(v))
        except ValueError:
            raise ValueError('argument to set_led_hsv must be parsable as three numbers (hue, saturation, value')
        config.hsv = h, s, v
        self._update_led(config)

    def set_led_rgb(self, led, r, g, b):
        try:
            r = _check_positive(float(r))
            g = _check_positive(float(g))
            b = _check_positive(float(b))
        except ValueError:
            raise ValueError('argument to set_led_rgb must be parsable as three numbers (red, green, blue)')
        self.set_led_hsv(led, *colorsys.rgb_to_hsv(r, g, b))

    def _update_led(self, config):
        h, s, v = config.hsv
        self._set_led_rgb(*colorsys.hsv_to_rgb(h, s, v * config.brightness))


def _check_positive(i):
    f = float(i)
    if f < 0.0:
        LOGGER.warning('Value < 0, returning 0')
        return 0.0
    if f > 1.0:
        LOGGER.warning('Value > 1.0, returning 1.0')
        return 1.0
    return f
