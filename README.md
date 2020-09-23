# Harware Support

**v0.1.10**

Allows you, as an expansion board creator, to only write the minimum logic to handle your motors,
servos, ADC channels, and LEDs, and provides:

1. Property based access, read and write, to each item
2. Per-item configuration for motors, servos, and ADC channels
3. Range checking on inputs
4. Colour, gamma, saturation correction, and brightness support for RGB LEDs based on either HSV / RGB tuples or CSS4 colour names
5. Caching on ADC channels
6. Configuration load / save for all per-item configuration settings

See `USAGE.md` for something you can give to your end users as a description of the
facilities this library will have added to your board.

## Usage

Call `add_properties` from within your `__init__` function. This will dynamically create
a new class with your object's class as a parent, and mix in the appropriate per-item
classes, as well as defining class level properties as appropriate. It then changes the
class of your object to that of the new class.

## GUI support

The `gui.run_curses_gui` function will introspect on your augmented object and create a
curses-based graphical interface providing interactive testing and configuration
for the facilities offered by your board (currently motors, servos and ADCs)