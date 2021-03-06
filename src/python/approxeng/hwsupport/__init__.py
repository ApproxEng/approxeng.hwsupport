# -*- coding: future_fstrings -*-

import logging

import yaml
from approxeng.hwsupport.adcs import ADCS, ADC, ReadADCsMixin
from approxeng.hwsupport.motors import MOTORS, Motor, SetMotorsMixin
from approxeng.hwsupport.servos import SERVOS, Servo, SetServosMixin
from approxeng.hwsupport.leds import LEDS, LED, SetLEDsMixin

LOGGER = logging.getLogger(name='approxeng.hwsupport')


def add_properties(board, motors=None, servos=None, adcs=None, default_adc_divisor=7891, leds=None):
    """
    Augment an existing instance of a motor, servo, adc, or combination driver class. This wraps up any provided
    methods in ones which check their input ranges properly, exposes those as properties (read and write), adds
    a set of configuration load and store methods, and also adds some generic functionality such as a stop() method.

    The exact properties and methods injected depend on the driver object passed in, and on the supplied lists of
    motors, servos, and adc channel numbers:

    For motors, the underlying board must provide a method _set_motor_speed(motor_index, speed) which accepts an integer
    motor number and a floating point value from -1.0 to 1.0 for speed. If this method exists, and there are items in
    the 'motors' parameter, then the following are added to the driver object:

    1. A new method set_motor_speed injected from the SetMotorsMixin. This takes the same arguments as the original
    _set_motor_speed method, but does value checking on both the motor index and the speed, and in addition tracks any
    requested speed changes to allow them to be read via property access.
    2. For each motor, a set of properties mXX and motorXX which allow write and read of that motor's speed value.
    3. For each motor, a set of properties mXX_invert and motorXX_invert which allow for negation of all values sent
    to subsequent motor speed calls - handy if you've not quite got your wiring right first time.
    4. For each motor, a set of properties mXX_scale and motorXX_scale which allow you to set the full scale range
    set for subsequent calls between 0.0 for no movement ever to 1.0 for full range.

    For servos, the underlying board must provide a method _set_servo_pulsewidth(servo, pulse_width) accepting an int
    servo index and a desired pulse width specified in microseconds. If this method exists, and there are items in the
    'servos' parameter, the following are added to the driver object:

    1. A new method, set_servo(servo, position), taking the integer index of a servo and a position in the range -1.0
    to 1.0. This method has error checking on the servo index, and will clamp its input position to the -1.0 to 1.0
    range silently.
    2. A new method, disable_servo(servo) which sets the pulse width of the given servo to 0.
    3. For each servo, a set of properties sXX and servoXX which allow read and write access to the servo position. If
    a servo is disabled these will read as None.
    4. For each servo, a set of properties sXX_config and servoXX_config which read and write a pair of values. These
    values are the minimum and maximum pulse widths accepted by the servo on this channel. These default to 500,2500
    unless otherwise set, and are used to interpret the position value of the servo when converting to a pulse width
    for the corresponding output.

    For ADC channels, the underlying board must provide a method _read_adc(adc) accepting an integer adc channel number
    and returning a raw ADC value. If this method exists and there are items in the 'adc' parameter, the following are
    added to the driver object:

    1. A new method, read_adc(adc), taking the same integer adc index as the underlying _read_adc method, and returning
    a floating point voltage. This voltage is calculated by dividing the raw read value by a per-adc-channel divisor.
    2. For each channel, an adcXX property which exposes the value for that channel.
    3. For each channel, an adcXX_divisor property which can be written and read to set and get the per-channel divisor
    4. For each channel, an adcXX_cache_time property, defaulting to 0 to disable caching, interpreted as a number of
    seconds for which reads should be cached and returned. This is particularly useful when an ADC channel is attached
    to a very slowly changing voltage such as a battery, allowing consumers of this API to read it within a control loop
    without creating excessive traffic to the ADC itself. It may also be necessary to prevent very rapid reads from ADC
    hardware unable to handle this.

    For LEDs, the underlying board must provide a method _set_led_rgb(led, r, g, b) taking RGB values as floats from 0.0
    to 1.0. If this method exists and there are entries in the 'leds' parameter, the following are added to the driver
    object:

    1. A new method, set_led_hsv(led, h, s, v) which does range checking on its hue, saturation, and value inputs - hue
    is treated as a continuous quantity so you can set it to anything, i.e. 1.0 is red, as is 0.0, as is 3.0 or -6.
    Saturation and value are clamped to 0.0-1.0
    2. A new method, set_led_brightness(led, brightness) which takes a brightness value from 0.0-1.0 and uses it to
    scale the value part of any colours set subsequently. Handy for when you don't want to blind yourself. Brightness
    is initially 1.0
    3. For each LED, a read / write property ledXX, this can be written to with either a tuple (h, s, v) or a colour
    name from the CSS4 standard colours. Reading the property will always return an HSV tuple
    4. For each LED, a read / write property ledXX_rgb, this can be written to with a tuple of 0.0-1.0 rgb values, and
    will return the same. Internally this is converted to HSV and scaled by the brightness, so your actual RGB values
    pushed to the LED may be different to those returned from this call if brightness is not 1.0
    5. For each LED, a read / write property ledXX_brightness which can be used to set the brightness for that LED from
    0.0 to 1.0
    6. For each LED, a read / write property ledXX_gamma which is used to apply a gamma correction function to the
    intensity of each R, G, B chip in the LED. Gamma of 2.0 is typical, defaults to 1.0 for no correction.
    7. For each LED, a read / write property ledXX_saturation which can be used to increase perceived saturation for
    paler colours, this applies a power of 1/value to the saturation component of each colour set, defaults to 1.0 for
    no correction, a value of 2 gives better pale colours when using the CSS4 colour names.


    Configuration properties are also injected, specifically a read / write property 'config' which contains the entire
    configuration for all motors, servos, and adc channels as a dict - writing to this property will only set values
    which exist both in the target object and in the supplied dict, it will ignore any properties not available to the
    object and does not require all properties to be set in one go. In addition a property 'config_yaml' allows the
    current configuration to be read into a YAML string.

    A method 'stop()' is also injected, this will set any motor speeds to zero, disable any servos, and then, if
    provided by the original object, call a '_stop()' function.

    Note - all injected methods take an optional **kwargs argument which will be passed through to the underlying
    object's methods.

    :param board:
        An instance of a motor, servo, adc or combo board object to be augmented. This object will be modified in place
    :param motors:
        An array of integer motor numbers to be exposed for this board, defaults to None for no motors
    :param servos:
        An array of integer servo numbers to be exposed for this board, defaults to None for no servos
    :param adcs:
        An array of integer ADC channel numbers to be exposed for this board, defaults to None for no ADC channels
    :param default_adc_divisor:
        Initial value for all ADC divisor configs, defaults to 7891
    """

    # Replace default values with empty lists
    if motors is None:
        motors = []
    if servos is None:
        servos = []
    if adcs is None:
        adcs = []
    if leds is None:
        leds = []

    # Construct a set of superclasses, applying mixins for each of motors, servos, and adc channels where present
    superclasses = [board.__class__]
    if callable(getattr(board, '_set_motor_speed', None)) and motors:
        superclasses += [SetMotorsMixin]
    if callable(getattr(board, '_set_servo_pulsewidth', None)) and servos:
        superclasses += [SetServosMixin]
    if callable(getattr(board, '_read_adc', None)) and adcs:
        superclasses += [ReadADCsMixin]
    if callable(getattr(board, '_set_led_rgb', None)) and leds:
        superclasses += [SetLEDsMixin]

    class Board(*superclasses):
        """
        There's exactly one instance of this class, it's created dynamically when augmenting an object with the
        motor, servo, and ADC properties.
        """

        def stop(self, **kwargs):
            """
            Used to stop all activity on a board.

            If there are servos, these are disabled. If there are motors, they are set to 0 speed. LEDs are disabled.
            Finally, if the underlying board's _stop() function is called, if present, to do any additional
            board-specific cleanup.
            """
            for motor in motors:
                self.set_motor_speed(motor, 0)
            for servo in servos:
                self.disable_servo(servo)
            for led in leds:
                self.set_led_hsv(led, 0, 0, 0)
            if callable(getattr(self, '_stop', None)):
                self._stop(**kwargs)

        @property
        def config(self):
            """
            Read out the servo, motor and ADC configuration as a dict
            """
            result = {}
            if ADCS in self._config:
                result[ADCS] = {index: a.config for index, a in self._config[ADCS].items()}
            if MOTORS in self._config:
                result[MOTORS] = {index: m.config for index, m in self._config[MOTORS].items()}
            if SERVOS in self._config:
                result[SERVOS] = {index: s.config for index, s in self._config[SERVOS].items()}
            return result

        @config.setter
        def config(self, d):
            """
            Set the servo, motor, and ADC configuration from a dict
            """
            if ADCS in d and ADCS in self._config:
                for index, a in d[ADCS].items():
                    if index in self._config[ADCS]:
                        self._config[ADCS][index].config = a
                    else:
                        LOGGER.warning(f'config contained ADC divisor for invalid index {index}')
            if MOTORS in d and MOTORS in self._config:
                for index, m in d[MOTORS].items():
                    if index in self._config[MOTORS]:
                        self._config[MOTORS][index].config = m
                    else:
                        LOGGER.warning(f'config contained motor invert for invalid index {index}')
            if SERVOS in d and SERVOS in self._config:
                for index, servo in d[SERVOS].items():
                    if index in self._config[SERVOS]:
                        self._config[SERVOS][index].config = servo
                    else:
                        LOGGER.warning(f'config contained servo configuration for invalid index {index}')

        def save_config(self, filename):
            """
            Write current configuration to the specified file
            """
            with open(filename, 'w') as file:
                yaml.dump(self.config, file)

        def load_config(self, filename):
            """
            Read configuration from the specified file
            """
            with open(filename) as file:
                self.config = yaml.load(file, Loader=yaml.FullLoader)

        @property
        def motors(self):
            """
            An array of motor indices. For a typical two-motor board this might be [0,1] or similar, in which case
            it would correspond to the injected m0, motor0, m1, motor1 etc properties
            """
            return motors

        @property
        def servos(self):
            """
            An array of servo indices, these correspond to the sXX, servoXX and sXX_config properties
            """
            return servos

        @property
        def adcs(self):
            """
            An array of ADC channel indices, corresponding to the adcXX and adcXX_divisor properties
            :return:
            """
            return adcs

        @property
        def leds(self):
            """
            An array of LED indices available to control
            :return:
            """
            return leds

        @property
        def config_yaml(self):
            """
            Config dict as a YAML string, set to update config from a YAML string.
            """
            return yaml.dump(self.config)

        @config_yaml.setter
        def config_yaml(self, yaml_string):
            self.config = yaml.load(yaml_string, Loader=yaml.FullLoader)

    # Set up configuration dict, we only add top level keys if the corresponding facility is requested
    config = {}
    if motors:
        config[MOTORS] = {}
    if servos:
        config[SERVOS] = {}
    if adcs:
        config[ADCS] = {}
    if leds:
        config[LEDS] = {}

    # Inject mXX, motorXX, mXX_invert, and motorXX_invert properties
    for motor in motors:
        m = Motor(motor=motor, invert=False, scale=1.0, board=board)
        config['motors'][motor] = m
        for prefix in ['m', 'motor']:
            setattr(Board, f'{prefix}{motor}', property(fget=m.get_value, fset=m.set_value))
            setattr(Board, f'{prefix}{motor}_invert', property(fset=m.set_invert, fget=m.get_invert))
            setattr(Board, f'{prefix}{motor}_scale', property(fset=m.set_scale, fget=m.get_scale))

    # Inject sXX, servoXX, sXX_config, and servoXX_config properties
    for servo in servos:
        s = Servo(servo=servo, pulse_min=500, pulse_max=2500, board=board)
        config['servos'][servo] = s
        for prefix in ['s', 'servo']:
            setattr(Board, f'{prefix}{servo}', property(fset=s.set_value, fget=s.get_value))
            setattr(Board, f'{prefix}{servo}_config', property(fset=s.set_config, fget=s.get_config))

    # Inject adcXX and adcXX_divisor properties
    for adc in adcs:
        a = ADC(adc=adc, divisor=default_adc_divisor, cache_time=0, board=board)
        config[ADCS][adc] = a
        setattr(Board, f'adc{adc}', property(fget=a.get_value))
        setattr(Board, f'adc{adc}_divisor', property(fset=a.set_divisor, fget=a.get_divisor))
        setattr(Board, f'adc{adc}_cache_time', property(fset=a.set_cache_time, fget=a.get_cache_time))

    # Inject ledXX, ledXX_brightness, ledXX_gamma, and ledXX_saturation properties
    for led in leds:
        l = LED(led=led, board=board)
        config[LEDS][led] = l
        setattr(Board, f'led{led}', property(fget=l.get_colour, fset=l.set_colour))
        setattr(Board, f'led{led}_brightness', property(fget=l.get_brightness, fset=l.set_brightness))
        setattr(Board, f'led{led}_gamma', property(fget=l.get_gamma, fset=l.set_gamma))
        setattr(Board, f'led{led}_saturation', property(fget=l.get_saturation, fset=l.set_saturation))
        setattr(Board, f'led{led}_rgb', property(fget=l.get_colour_rgb, fset=l.set_colour_rgb))

    # Set the supplied object's class to the newly created subclass
    board._config = config
    board.__class__ = Board
