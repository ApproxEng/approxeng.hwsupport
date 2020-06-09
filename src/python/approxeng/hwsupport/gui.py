# -*- coding: future_fstrings -*-

import curses
import curses.textpad
from math import floor

DEFAULT_MOTOR_KEYS = ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']')
DEFAULT_SERVO_KEYS = ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", '#')
DEFAULT_ADC_KEYS = ('z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/')
DEFAULT_TITLE = 'Approxeng.hwsupport console by @Approx_Eng'

VALUE_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-']
VALUE_ITEMS = list([round(i / ((len(VALUE_KEYS) - 1) / 2) - 1, 1) for i in range(0, len(VALUE_KEYS))])


def run_curses_gui(board, motor_keys=DEFAULT_MOTOR_KEYS, servo_keys=DEFAULT_SERVO_KEYS, adc_keys=DEFAULT_ADC_KEYS,
                   title=DEFAULT_TITLE):
    """
    Build and run the GUI for the supplied board. See build_curses_gui for parameter documentation
    """
    curses.wrapper(build_curses_gui(board, motor_keys, servo_keys, adc_keys, title))


def build_curses_gui(board, motor_keys=DEFAULT_MOTOR_KEYS, servo_keys=DEFAULT_SERVO_KEYS, adc_keys=DEFAULT_ADC_KEYS,
                     title=DEFAULT_TITLE):
    """
    Build the GUI for a given board instance.
    :param board:
        A board which must have been augmented by the approxeng.hwsupport module
    :param motor_keys:
        Keys used to select motor driver channels, defaults to the QWERTYUIOP[] row on the keyboard. Must contain at
        least as many items as you have motor driver channels, only those corresponding to motor drivers on the supplied
        board will be shown.
    :param servo_keys:
        Keys used to select servos, defaults to the ASDFGHKL;'# row on the keyboard. Must contain at least as many items
        as you have servos, only those corresponding to servos on the supplied board will be shown.
    :param adc_keys:
        Keys used to select ADC channels, defaults to ZXCVBNM,./ row on the keyboard. Must contain at least as many
        items as you have ADCs, only those corresponding to ADCs on the supplied board will be shown.
    :param title:
        Shown on the first line of the generated console
    :return:
        A function which can be used as the argument to curses.wrapper(..) to show the GUI
    """

    def curses_main(screen):
        try:
            display = DisplayState(screen=screen, board=board, motor_keys=motor_keys, servo_keys=servo_keys,
                                   adc_keys=adc_keys)
            curses.cbreak()
            curses.halfdelay(1)
            while True:
                display.start()

                # Draw title
                display.println(title)
                display.println('Letters to select control, numbers to set value, SPACE stops all, CTRL-C to exit')
                display.newline()

                # Motors, if present
                if display.motors:
                    display.print_header('Motors')
                    for index, motor in enumerate(display.motors):
                        row, col = divmod(index, 4)
                        display.show_motor(display.line + row, col * 20, motor)
                    display.line += floor((len(display.motors) - 1) / 4) + 1
                    display.newline()

                # Servos, if present
                if display.servo_pins:
                    display.print_header('Servos')
                    for index, servo in enumerate(display.servo_pins):
                        row, col = divmod(index, 4)
                        display.show_servo(display.line + row, col * 20, servo)
                    display.line += floor((len(display.servo_pins) - 1) / 4) + 1
                    display.newline()

                # ADC channels, if present
                if display.adcs:
                    display.print_header('ADC Channels')
                    for index, adc in enumerate(display.adcs):
                        row, col = divmod(index, 4)
                        display.show_adc(display.line + row, col * 20, adc)
                    display.line += floor((len(display.adcs) - 1) / 4) + 1
                    display.newline()

                # Show values if either motor or servo, doesn't make any sense for e.g. ADCs
                if display.control_is_servo or display.control_is_motor:
                    display.println('Values - number key row or up / down arrows to set, BACKSPACE to stop / disable')
                    for value in VALUE_ITEMS:
                        index = VALUE_ITEMS.index(value)
                        display.show_value(display.line + len(VALUE_ITEMS) - index - 1, 2, value)

                # Show editor if the selected control has one
                if display.control_is_servo:
                    editor = ServoConfigEditor(display=display, row=display.line + 1, column=40, height=4)
                    editor.render()
                elif display.control_is_motor:
                    editor = MotorConfigEditor(display=display, row=display.line + 1, column=40, height=3)
                    editor.render()
                elif display.control_is_adc:
                    editor = ADCConfigEditor(display=display, row=display.line, column=40, height=3)
                    editor.render()
                else:
                    editor = None

                # Wait for a keypress and respond to it
                try:
                    key = screen.getkey()
                    if key in motor_keys and motor_keys.index(key) < board.num_motors:
                        display.control = f'm{display.motors[motor_keys.index(key)]}'
                    elif key in servo_keys and servo_keys.index(key) < len(display.servo_pins):
                        display.control = f's{display.servo_pins[servo_keys.index(key)]}'
                    elif key in adc_keys and adc_keys.index(key) < len(display.adcs):
                        display.control = f'adc{display.adcs[adc_keys.index(key)]}'
                    elif key == ' ':
                        board.stop()
                    elif key == 'KEY_LEFT':
                        display.select_previous_control()
                    elif key == 'KEY_RIGHT':
                        display.select_next_control()
                    elif key == '=' and editor is not None:
                        editor.edit()
                        curses.cbreak()
                        curses.halfdelay(1)
                    elif key == 'KEY_BACKSPACE':
                        if display.control_is_servo:
                            display.value = None
                        elif display.control_is_motor:
                            display.value = 0
                    # Setting value is only meaningful if we've got a servo or motor selected
                    if display.control_is_servo or display.control_is_motor:
                        if key in VALUE_KEYS:
                            display.value = VALUE_ITEMS[VALUE_KEYS.index(key)]
                        elif key == 'KEY_UP':
                            display.value = round(min(display.value + 0.2, 1.0), 1) if display.value is not None else 0
                        elif key == 'KEY_DOWN':
                            display.value = round(max(display.value - 0.2, -1.0), 1) if display.value is not None else 0
                except curses.error:
                    # No input available, perfectly normal
                    pass
        except KeyboardInterrupt:
            # Exit on CTRL-C, stopping the motors as we go
            board.stop()

    return curses_main


class DisplayState:

    def __init__(self, screen, board, motor_keys, servo_keys, adc_keys):
        self.screen = screen

        self.line = 0
        self.servo_pins = board.servos
        self.board = board
        self.adcs = board.adcs
        self.motors = board.motors
        self.motor_keys = motor_keys
        self.servo_keys = servo_keys
        self.adc_keys = adc_keys
        self.all_controls = list([f'm{motor}' for motor in self.motors]) + list(
            [f's{servo}' for servo in self.servo_pins]) + list([f'adc{adc}' for adc in self.adcs])
        self.control = self.all_controls[0]
        # Disable echo to terminal
        curses.noecho()
        # Hide the cursor
        curses.curs_set(0)
        # Contrast colour for UI
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # Highlight
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        # Enable colour
        curses.start_color()
        # Clear the screen
        screen.clear()
        # Enable key events for special keys i.e. arrows, backspace
        screen.keypad(True)

    def start(self):
        self.screen.clear()
        self.line = 0

    @property
    def value(self):
        return self.board.__getattribute__(self.control)

    @value.setter
    def value(self, value):
        self.board.__setattr__(self.control, value)

    def println(self, string, contrast=False):
        try:
            if contrast:
                self.screen.addstr(self.line, 0, string, curses.color_pair(1))
            else:
                self.screen.addstr(self.line, 0, string)
        except curses.error:
            pass
        self.line += 1

    def select_next_control(self):
        control_index = self.all_controls.index(self.control)
        self.control = self.all_controls[(control_index + 1) % len(self.all_controls)]

    def select_previous_control(self):
        control_index = self.all_controls.index(self.control)
        self.control = self.all_controls[(control_index - 1) % len(self.all_controls)]

    def newline(self):
        self.line += 1

    def print_header(self, string):
        s = '——' + string
        s += '—' * (80 - len(s))
        self.println(s, True)

    def show_motor(self, row, col, motor):
        try:
            try:
                speed = self.board.__getattribute__(f'm{motor}')
            except AttributeError:
                speed = None
            speed_string = '??' if speed is None else f'{speed:.1f}'
            rep = f'm{motor}[{self.motor_keys[motor]}] = {speed_string}'
            if self.control == f'm{motor}':
                self.screen.addstr(row, col, rep, curses.color_pair(2))
            else:
                self.screen.addstr(row, col, rep)
        except curses.error:
            pass

    @property
    def control_is_servo(self):
        return self.control[:1] == 's'

    @property
    def control_is_motor(self):
        return self.control[:1] == 'm'

    @property
    def control_is_adc(self):
        return self.control[:1] == 'a'

    def show_servo(self, row, col, servo):
        try:
            try:
                value = self.board.__getattribute__(f's{servo}')
            except AttributeError:
                value = None
            value_string = '--' if value is None else f'{value:.1f}'
            rep = f's{servo:02}[{self.servo_keys[self.servo_pins.index(servo)]}] = {value_string}'
            if self.control == f's{servo}':
                self.screen.addstr(row, col, rep, curses.color_pair(2))
            else:
                self.screen.addstr(row, col, rep)
        except curses.error:
            pass

    def show_adc(self, row, col, adc):
        try:
            try:
                value = self.board.__getattribute__(f'adc{adc}')
            except AttributeError:
                value = None
            value_string = '--' if value is None else f'{value:.2f}'
            rep = f'adc{adc:01}[{self.adc_keys[self.adcs.index(adc)]}] = {value_string}v'
            if self.control == f'adc{adc}':
                self.screen.addstr(row, col, rep, curses.color_pair(2))
            else:
                self.screen.addstr(row, col, rep)
        except curses.error:
            pass

    def show_value(self, row, col, value):
        try:
            current_value = self.value
            string = f'[{VALUE_KEYS[VALUE_ITEMS.index(round(value, 1))]}]={round(value, 1)}'
            if current_value is not None and round(current_value, 1) == round(value, 1):
                self.screen.addstr(row, col, string, curses.color_pair(2))
            else:
                self.screen.addstr(row, col, string)
        except curses.error:
            pass


class MotorConfigEditor:
    def __init__(self, display, row, column, height):
        self.display = display
        self.row = row
        self.column = column
        self.height = height

    def render(self):
        try:
            screen = self.display.screen
            curses.textpad.rectangle(screen, self.row, self.column, self.row + self.height, 79)
            screen.addstr(self.row + 1, self.column + 1, f'Motor {self.display.control}, \'=\' to toggle invert:',
                          curses.color_pair(1))
            invert = self.display.board.__getattribute__(f'{self.display.control}_invert')
            screen.addstr(self.row + 2, self.column + 1, f'Invert direction = {invert}')
        except curses.error:
            pass

    def edit(self):
        invert = self.display.board.__getattribute__(f'{self.display.control}_invert')
        self.display.board.__setattr__(f'{self.display.control}_invert', not invert)


class ADCConfigEditor:
    def __init__(self, display, row, column, height):
        self.display = display
        self.row = row
        self.column = column
        self.height = height

    def render(self):
        try:
            screen = self.display.screen
            curses.textpad.rectangle(screen, self.row, self.column, self.row + self.height, 79)
            screen.addstr(self.row + 1, self.column + 1, f'ADC {self.display.control}, \'=\' to calibrate:',
                          curses.color_pair(1))
            divisor = self.display.board.__getattribute__(f'{self.display.control}_divisor')
            screen.addstr(self.row + 2, self.column + 1, f'Current divisor = {divisor:.1f}')
        except curses.error:
            pass

    def edit(self):
        try:
            screen = self.display.screen
            screen.addstr(self.row + 1, self.column + 1, f'Enter observed voltage, then RETURN:  ',
                          curses.color_pair(1))
            screen.addstr(self.row + 2, self.column + 1, f'Measured voltage =                    ')
            curses.echo()
            curses.curs_set(2)
            measured_voltage = screen.getstr(self.row + 2, self.column + 20, 10)

            parsed_measured_voltage = None
            try:
                parsed_measured_voltage = float(measured_voltage)
            except ValueError:
                pass
            if parsed_measured_voltage:
                current_voltage = self.display.value
                current_divisor = self.display.board.__getattribute__(f'{self.display.control}_divisor')
                new_divisor = current_divisor * (current_voltage / parsed_measured_voltage)
                self.display.board.__setattr__(f'{self.display.control}_divisor', new_divisor)
            curses.noecho()
            curses.curs_set(0)
        except curses.error:
            curses.noecho()
            curses.curs_set(0)


class ServoConfigEditor:
    def __init__(self, display, row, column, height):
        self.display = display
        self.row = row
        self.column = column
        self.height = height

    def render(self):
        try:
            screen = self.display.screen
            curses.textpad.rectangle(screen, self.row, self.column, self.row + self.height, 79)
            screen.addstr(self.row + 1, self.column + 1, f'Servo {self.display.control}, \'=\' to edit config:',
                          curses.color_pair(1))
            pulse_min, pulse_max = self.display.board.__getattribute__(f'{self.display.control}_config')
            screen.addstr(self.row + 2, self.column + 1, f'Min pulse width = {pulse_min} μs')
            screen.addstr(self.row + 3, self.column + 1, f'Max pulse width = {pulse_max} μs')
        except curses.error:
            pass

    def edit(self):
        try:
            screen = self.display.screen
            screen.addstr(self.row + 1, self.column + 1, f'Enter new Pulse Min, then RETURN:   ',
                          curses.color_pair(1))
            screen.addstr(self.row + 2, self.column + 1, f'Min pulse width =                 ')
            curses.echo()
            curses.curs_set(2)
            new_min = screen.getstr(self.row + 2, self.column + 19, 10)
            screen.addstr(self.row + 1, self.column + 1, f'Enter new Pulse Max, then RETURN:',
                          curses.color_pair(1))
            screen.addstr(self.row + 3, self.column + 1, f'Max pulse width =                 ')
            new_max = screen.getstr(self.row + 3, self.column + 19, 10)
            parsed_new_min = None
            parsed_new_max = None
            try:
                parsed_new_min = int(new_min)
            except ValueError:
                pass
            try:
                parsed_new_max = int(new_max)
            except ValueError:
                pass
            self.display.board.__setattr__(f'{self.display.control}_config', (parsed_new_min, parsed_new_max))
            curses.noecho()
            curses.curs_set(0)
        except curses.error:
            curses.noecho()
            curses.curs_set(0)
