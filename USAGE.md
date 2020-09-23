# Usage

**v0.1.12**

All hardware using the `approxeng.hwsupport` library presents a set of consistent functions and properties that you
can use in your code. This page describes how you can use this standard API to access the specific hardware on your
particular board, HAT, or similar.

Note that while this library allows for multiple different kinds of hardware (motors, servos, ADC channels, LEDs) your
board may well only support some of these. If your board doesn't have, for example, an ADC module then you won't see
the ADC properties. You can't use what you don't have!

If you've been directed here from your hardware's documentation it means that you can use some or all of the API here
to drive your hardware, see below for details on exactly how to do that. It is assumed here that you've already
created an instance of your hardware's driver class, called `board`.

## Motors

If your board has DC motor support, the following function will be available:

```python
# motor_id : integer describing which motor to control
# speed    : floating point value between -1.0 and 1.0 inclusive
board.set_motor_speed(motor_id, speed) 
```

In addition, for each motor, you can access motor speed, scaling, and invert configuration through properties:

```python
# This example uses motor number 3, consult your board
# documentation for how these numbers relate to output
# pins or terminals on your particular hardware!

# Set motor speed, values between -1.0 and 1.0 as before
board.m3 = speed

# Set whether the motor speed is inverted, use if your
# motor turns the wrong way!
board.m3_invert = True

# Scale the maximum output, can be handy if you know you
# want to limit to e.g. half speed when speed is set to 1.0
board.m3_scale = 0.5

# You can also use motor3 in place of m3 if you prefer
board.motor3 = speed
board.motor3_invert = True
board.motor3_scale = 0.5
```

All properties are readable as well as writeable, and both they and the `set_motor_speed` function perform range
checks on the speed value provided. If you attempt to set a value higher than `1.0` it will be set to `1.0`, and 
similarly for values lower than `-1.0`.

## Servos

If your motor has servo support, the following functions will be available:

```python
# servo_id : integer describing which servo to control
# position : floating point value between -1.0 and 1.0 inclusive
board.set_servo(servo_id, position)

# servo_id : integer describing which servo to control
board.disable_servo(servo_id)
```

In addition, for each servo, you can access position and pulse width configuration through properties:

```python
# This example uses servo number 17, consult your board
# documentation for how these numbers relate to output
# pins or terminals on your particular hardware!

# Set servo position
board.s17 = position

# Disable a servo
board.s17 = None

# Configure minimum / maximum pulse length in microseconds
# This defaults to 1500, 2500 but many servos will need a
# smaller range, i.e. to set min=1600 and max=2400
board.s17_config = 1600, 2400

# As with motors, you can use servo17 in place of s17 if you prefer
board.servo17 = position
board.servo17_config = 1600, 2400
```

As with motors, all properties are readable as well as writeable, and all perform range checking.

## Analogue / Digital Converter channels (ADCs)

If your board has ADC channels, the following function will be available:

```python
# adc_id : integer describing the ADC channel to read
# digits : desired precision of the reading, defaults to 2 for 2 decimal places  
board.read_adc(adc_id, digits)
```

In addition, for each ADC channel, you can read the value and configure scaling and cacheing through properties:

```python
# This example uses ADC channel number 5, consult your board
# documentation for how these numbers relate to input pins or
# terminals on your particular hardware!

# Read the value from an ADC channel, uses the default 2 digit
# precision when getting the value.
some_voltage = board.adc5

# Set the divisor, this is the value that's used to get a real
# voltage from the value read by the ADC. Your board will set
# sensible defaults for this, but you can use it to calibrate
# or compensate for e.g. reading from a voltage divider. The
# calculation is:
#
# reading = adc_raw_value / divisor
board.adc5_divisor = 1200

# Set the cache time. If this is non-zero, after a value is read from
# the hardware then all subsequent requests will return that value until
# this time is exceeded. This is useful when your measured value changes
# very slowly and you want to avoid making too many requests to the 
# hardware. For example, if we're monitoring a battery we only want to
# read the voltage at most every ten seconds. Set to 0 to disable caching.
board.adc5_cache_time = 10
```

As above, `cache_time` and `divisor` properties are also readable. This is particularly useful for the divisor,
as you can calibrate you readings by reading off the current divisor, working out how much your reading is out
compared to a reference (e.g. using a multimeter to measure the actual voltage) and then adjusting the divisor
so that the reading is accurate. You might use code like this:

```python
# The value we recorded with a multi-meter
actual_voltage = 12.8

# Use the ADC channel to measure the observed voltage
reading = board.adc5

# Divide to get the error, i.e. if the reading is half the
# recorded value this will be 0.5. This is the amount we need
# to multiply the divisor by to calibrate
ratio = reading / actual_voltage

# Set the new divisor, because it's a readable property we can
# use operators like += and *= to update it
board.adc5_divisor *= ratio
```

## LEDs

If your board has multicolour (RGB) LEDs on board, the following functions will be available:

```python
# Set the colour using HSV space
#
# led_id     : integer ID of the LED to control
# hue        : hue, from 0.0 to 1.0 but other values round to
#              this range as hue is a circular quantity, so 1.5
#              and 0.5 are the same colour. 0.0 is red
# saturation : saturation, from 0.0 (no colour) to 1.0 (full colour)
# value      : brightness, from 0.0 (off) to 1.0 (full on)
board.set_led_hsv(led_id, hue, saturation, value)

# Set the colour using RGB space
#
# led_id : integer ID of the LED to control
# red    : red component, 0.0 to 1.0
# green  : green component, 0.0 to 1.0
# blue   : blue component, 0.0 to 1.0
board.set_led_rgb(led_id, red, green, blue)

# Set the brightness of the LED, useful because often RGB LEDs
# are unusably bright at full power, this preserves colour but
# reduces the eye-melting property of these devices
#
# led_id     : integer ID of the LED to control
# brightness : float from 0.0 to 1.0
board.set_led_brightness(led_id, brightness)

# Set the saturation compensation of the LED, used to boost the
# degree of colour in paler colours so they don't all look white
# 
# led_id     : integer ID of the LED to control
# saturation : saturation from 0.0 (black and white) upwards. 1.0
#              equates to no compensation, 2.0-3.0 seems a decent
#              default value
board.set_led_saturation(led_id, saturation)

# Set the gamma conpensation of the LED, used to give a linear
# intensity response as brightness is increased. Without this
# the LED intensity distribution is weighted heavily towards
# low or high values, with only a small portion of the control
# range having a visible effect
#
# led_id : integer ID of the LED to control
# gamma  : gamma value, 1.0 for no correction
board.set_led_gamma(led_id, gamma)
```

These are also available as properties:

```python
# This example uses LED number 2, consult your board
# documentation for how these numbers relate to LEDs
# on your particular hardware

# Set colour using HSV
board.led2 = hue, saturation, value

# Set colour using CSS4 colour name
board.led2 = 'pink'

# NOTE - whether you set this by HSV or by name, reading
# this property always returns a (hue, saturation, value)
# tuple.

# Set colour using RGB
board.led2_rgb = red, green, blue

# Set brightness
board.led2_brightness = 0.7

# Set gamma
board.led2_gamma = 1.9

# Set saturation
board.led2_saturation = 3.0
```

See https://www.w3.org/TR/css-color-4/#named-colors for the full list of CSS4 colour names, you can use any of these
in your LED colours.

## Discovering Capabilities

You can probably tell how many of each function you have by looking at your
hardware. If you want to find that information from your code (for example,
you're writing code that runs on any board with at least four motors and want
to check whether this particular hardware has that) you can use the following
properties:

```python
# An array of motor IDs
board.motors

# An array of servo IDs
board.servos

# An array of ADC channel IDs
board.adcs

# An array of LED IDs
board.leds
```

If your hardware doesn't support any of a facility, that corresponding property will
return an empty list. Because empty lists are `False` you can do something like this:

```python
if board.motors:
    print(f'Found some motors: {",".join(board.motors)}')
else:
    print('No motors found')
```

## Shutdown Function

Your board will have a function that shuts down all its facilities. This means motors will stop,
servos will be disabled, and LEDs turned off. This function is present whether you have any of
these capabilities or not, and the specific board driver may use it to do other cleanup.

```python
board.stop()
```

## Configuration

Some facilities, most obviously motors, servos and ADC channels, have configuration associated with
them. You can get and set this configuration as a python `dict`

```python
# get the configuration of everything as a dict
config_as_dict = board.config

# ...and set it from one
board.config = new_config_as_dict
```

You can also get and set the config from a YAML string, this is a more compact and generally human-readable
format but otherwise identical to the `dict` above

```python
# get the configuration as a YAML string
yaml = board.config_yaml

# set the configuration from a YAML string
board.config_yaml = new_yaml
```

In addition, there are two convenience methods that handle writing and reading the configuration to files
in YAML format

```python
# Write out configuration to a file
#
# filename : file to write
board.save_config(filename)

# Read configuration from a previously written file
# 
# filename: file to read
board.load_config(filename)
```

The board creator should have set sensible default configuration properties that match the hardware, so
you can always get and / or save a configuration to a file immediately after creating a new instance of
the board object.

## Hardware Console

Your board creator may have used the facilities here to build a graphical console that can help you
test and configure motors, servos, and ADC channels (if you have them!). See the documentation provided
by the board creator on how to launch this console. Typically you will use the console to interactively
test motors and servos, and to set things like ADC calibration and servo pulse ranges to values that match
your particular use. The GUI can be configured by the board creator to emit a configuration file in YAML
form that you can then load into your own code on startup. This is designed so you can use the GUI to
configure everything, then have those configuration settings available in your own code at a later point.