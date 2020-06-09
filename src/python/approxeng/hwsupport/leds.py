# -*- coding: future_fstrings -*-

import colorsys
import logging

from approxeng.hwsupport.css4_colours import CSS4_COLOURS
from approxeng.hwsupport.util import check_positive

LOGGER = logging.getLogger(name='approxeng.hwsupport.leds')

LEDS = 'leds'


class LED:
    def __init__(self, led, board):
        self.led = led
        self.board = board
        self.brightness = 1.0
        self.gamma = 1.0
        self.saturation = 1.0
        self.hsv = (0, 0, 0)

    def set_colour(self, _, value):
        if isinstance(value, tuple):
            self.board.set_led_hsv(self.led, *value)
        elif value in CSS4_COLOURS:
            self.board.set_led_hsv(self.led, *CSS4_COLOURS[value])
        else:
            LOGGER.warning(f'colour for led{self.led} is neither a triple or a colour name')

    def set_gamma(self, _, value):
        self.gamma = float(value)
        self.board._update_led(self)

    def get_gamma(self, _):
        return self.gamma

    def set_saturation(self, _, value):
        self.saturation = float(value)
        self.board._update_led(self)

    def get_saturation(self, _):
        return self.saturation

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
        config.brightness = check_positive(brightness)
        self._update_led(config)

    def set_led_hsv(self, led, h, s, v):
        config = self._check_led_index(led)
        try:
            h = float(h) % 1.0
            s = check_positive(float(s))
            v = check_positive(float(v))
        except ValueError:
            raise ValueError('argument to set_led_hsv must be parsable as three numbers (hue, saturation, value')
        config.hsv = h, s, v
        self._update_led(config)

    def set_led_rgb(self, led, r, g, b):
        try:
            r = check_positive(float(r))
            g = check_positive(float(g))
            b = check_positive(float(b))
        except ValueError:
            raise ValueError('argument to set_led_rgb must be parsable as three numbers (red, green, blue)')
        self.set_led_hsv(led, *colorsys.rgb_to_hsv(r, g, b))

    def _update_led(self, config):
        h, s, v = config.hsv
        v = v * config.brightness
        s = s ** (1 / config.saturation) if config.saturation > 0 else 0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self._set_led_rgb(config.led, r ** config.gamma, g ** config.gamma, b ** config.gamma)
