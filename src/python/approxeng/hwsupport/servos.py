import logging

from approxeng.hwsupport import check_range

LOGGER = logging.getLogger(name='approxeng.hwsupport.servos')
SERVOS = 'servos'


class Servo:
    """
    Holds configuration for a servo pin
    """

    def __init__(self, servo, pulse_min, pulse_max, board):
        self.servo = servo
        self.pulse_max = pulse_max
        self.pulse_min = pulse_min
        self.value = None
        self.board = board

    def set_value(self, _, value):
        if value is not None:
            self.board.set_servo(servo=self.servo, position=value)
        else:
            self.board.disable_servo(servo=self.servo)

    def get_value(self, _):
        return self.value

    def set_config(self, _, value):
        new_pulse_min, new_pulse_max = value
        if new_pulse_min is not None and not isinstance(new_pulse_min, int):
            raise ValueError(f'pulse_min must be None or int, was {new_pulse_min}')
        if new_pulse_max is not None and not isinstance(new_pulse_max, int):
            raise ValueError(f'pulse_max must be None or int, was {new_pulse_max}')
        self.pulse_min = new_pulse_min or self.pulse_min
        self.pulse_max = new_pulse_max or self.pulse_max
        # PiGPIO won't allow values <500 or >2500 for this, so we clamp them here
        self.pulse_max = min(self.pulse_max, 2500)
        self.pulse_min = max(self.pulse_min, 500)
        if self.value is not None:
            # If we have an active value set then update based on the new
            # configured pulse min / max values
            self.set_value(_, self.value)

    def get_config(self, _):
        return self.pulse_min, self.pulse_max


class SetServosMixin:
    """
    Mixed into the new class used for the augmented instance to provide the set_servo and disable_servo methods
    """

    def _check_servo_index(self, servo):
        """
        Check that a servo is valid, raising ValueError if not and returning the config otherwise.
        """
        if SERVOS not in self._config:
            raise ValueError(f'board has no servo functions, unable to set  / disable s{servo}')
        if servo not in self._config[SERVOS]:
            raise ValueError(f'servo s{servo} not in {list(self._config[SERVOS].keys())}')
        return self._config[SERVOS][servo]

    def set_servo(self, servo: int, position: float, **kwargs):
        """
        Set a servo value

        :param servo:
            The servo to set, this must be a value in the array of servos
        :param position:
            Position from -1.0 (minimum PWM duty cycle) to 1.0 (max PWM). Values outside this range will be clamped to
            it
        :param kwargs:
            Any additional arguments to provide to the underlying _set_servo_pulsewidth method
        :raises:
            ValueError if the supplied servo index isn't available, or there are no servos defined for this board,
            or the position supplied is not a non-None int or float value
        """
        if position is None:
            raise ValueError(f'position for s{servo} must not be None')
        if not isinstance(position, (float, int)):
            raise ValueError(f's{servo} value must be float, was {position}')
        LOGGER.debug(f'set servo s{servo}={position}')
        config = self._check_servo_index(servo)
        position = check_range(position)
        pulse_min, pulse_max = config.pulse_min, config.pulse_max
        config.value = position
        position = -position
        scale = float((pulse_max - pulse_min) / 2)
        centre = float((pulse_max + pulse_min) / 2)
        self._set_servo_pulsewidth(servo, int(centre - scale * position), **kwargs)

    def disable_servo(self, servo: int, **kwargs):
        """
        Set a servo PWM duty cycle to 0, releasing control

        :param servo:
            The servo to set, this must be a value in the array of servos
        :param kwargs:
            Any additional arguments to provide to the underlying _set_servo_pulsewidth method
        :raises:
            ValueError if the supplied servo index isn't available, or there are no servos defined for this board
        """
        LOGGER.debug(f'disable servo s{servo}')
        config = self._check_servo_index(servo)
        config.value = None
        self._set_servo_pulsewidth(servo, 0, **kwargs)
