# -*- coding: future_fstrings -*-

import logging

from approxeng.hwsupport.util import check_range, check_positive_range

LOGGER = logging.getLogger(name='approxeng.hwsupport.motors')
MOTORS = 'motors'


class Motor:
    """
    Holds configuration for a motor. You won't use this class directly.
    """

    def __init__(self, motor, invert, scale, board):
        self.motor = motor
        self.invert = invert
        self.scale = scale
        self.board = board
        self.value = None

    @property
    def config(self):
        return {'invert': self.invert, 'scale': self.scale}

    @config.setter
    def config(self, d):
        if 'invert' in d:
            self.set_invert(None, d['invert'])
        if 'scale' in d:
            self.set_scale(None, d['scale'])

    def set_value(self, _, value):
        self.board.set_motor_speed(motor=self.motor, speed=value * self.scale)

    def get_value(self, _):
        return self.value

    def set_invert(self, _, value):
        if value is None or not isinstance(value, bool):
            raise ValueError(f'm{self.motor}_invert must be True|False, was {value}')
        self.invert = value
        if self.value is not None:
            self.board.set_motor_speed(motor=self.motor, speed=self.value * self.scale)

    def get_invert(self, _):
        return self.invert

    def set_scale(self, _, value):
        if value is not None and isinstance(value, int):
            value = float(value)
        if value is None or not isinstance(value, float):
            raise ValueError(f'm{self.motor}_scale must be a floating point value, was {value}')
        self.scale = check_positive_range(value)
        if self.value is not None:
            self.board.set_motor_speed(motor=self.motor, speed=self.value * self.scale)

    def get_scale(self, _):
        return self.scale


class SetMotorsMixin:
    """
    Mixed into the new class used for the augmented instance to provide the set_motor_speed method
    """

    def set_motor_speed(self, motor: int, speed: float, **kwargs):
        """
        Set a motor speed

        :param motor:
            The motor to set, this must be a value in the array of motor indices
        :param speed:
            Speed from -1.0 to 1.0, values outside this range will be clamped to it
        :param kwargs:
            Any additional arguments to be passed to the underlying _set_motor_speed method defined on the original
            instance pre-augmentation
        :raises:
            ValueError if motors are defined but the supplied index isn't in the array, or no motors are defined.
        """
        if MOTORS in self._config:
            LOGGER.debug(f'set motor m{motor}={speed}')
            if motor not in self._config[MOTORS]:
                raise ValueError(f'motor m{motor} not in {list(self._config[MOTORS].keys())}')
            speed = check_range(speed)
            config = self._config[MOTORS][motor]
            config.value = speed
            self._set_motor_speed(motor, speed if not config.invert else -speed, **kwargs)
        else:
            raise ValueError(f'board has no motor functions, unable to set m{motor}')
