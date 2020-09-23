from approxeng.hwsupport import add_properties
import logging

LOGGER = logging.getLogger('demo')
logging.basicConfig(level=logging.DEBUG)


class LoggingMotorBoard:
    """
    A fake driver board that just logs values that would normally be set.
    """

    def __init__(self):
        """
        Create the instance. Do any board-specific setup (we don't have any here)
        and then call the add_properties function to augment this instance with
        extra properties, config etc.
        """
        LOGGER.info('Created new LoggingMotorBoard instance')
        # Motors, servos, adcs, and leds are optional, include those for your hardware
        # and implement the corresponding private methods as shown below. This example
        # includes a couple of motors, four servos (note that numbers do not have to be
        # consecutive), three ADC channels and a pair of LEDs
        add_properties(board=self,
                       motors=[0, 1],
                       servos=[0, 1, 5, 6],
                       adcs=[0, 1, 2],
                       leds=[0, 1])

    def _set_motor_speed(self, motor, speed: float):
        """
        :param motor:
            Number of the motor to set, this matches the values in 'motors=[0, 1]' above
        :param speed:
            Value between -1.0 and 1.0
        """
        LOGGER.info(f'Setting motor {motor} to speed {speed}')

    def _set_servo_pulsewidth(self, servo, pulse_width):
        """
        :param servo:
            Number of the servo to set, this matches the values in 'servos=[0, 1, 5, 6] above
        :param pulse_width:
            Pulse width in microseconds
        """
        LOGGER.info(f'Setting servo {servo} pulse width to {pulse_width} microseconds')

    def _read_adc(self, adc):
        """
        :param adc:
            Number of the ADC channel to read, matches values in 'adcs=[0, 1, 2]' above
        :return:
            The raw value from the ADC channel
        """
        LOGGER.info(f'Reading from ADC channel {adc}, returning 12345')
        return 12345

    def _set_led_rgb(self, led, red, green, blue):
        """
        :param led:
            Number of the LED to set, matches values in 'leds=[0, 1]' above
        :param red:
            Red, 0.0-1.0
        :param green:
            Green, 0.0-1.0
        :param blue:
            Blue, 0.0-1.0
        """
        LOGGER.info(f'Setting LED {led}, RGB=({red}, {green}, {blue})')

    def _stop(self):
        """
        Called after motors are shut down and LEDs and servos disabled
        """
        LOGGER.info(f'Shutting down')


b = LoggingMotorBoard()
b.m0 = 1
b.led1 = 'pink'
b.servo0_config = 700, 1000
b.s0 = 1
print(b.config)
b.stop()
