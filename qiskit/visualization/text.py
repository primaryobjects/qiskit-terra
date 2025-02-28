# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
A module for drawing circuits in ascii art or some other text representation
"""

from warnings import warn
from shutil import get_terminal_size
import sys

from qiskit.circuit import Clbit
from qiskit.circuit import ControlledGate
from qiskit.circuit import Reset
from qiskit.circuit import Measure
from qiskit.circuit.library.standard_gates import IGate, RZZGate, SwapGate, SXGate, SXdgGate
from qiskit.circuit.tools.pi_check import pi_check
from qiskit.visualization.utils import get_gate_ctrl_text, get_param_str, get_bit_label
from .exceptions import VisualizationError


class TextDrawerCregBundle(VisualizationError):
    """The parameter "cregbundle" was set to True in an impossible situation. For example,
    a node needs to refer to individual classical wires'"""

    pass


class TextDrawerEncodingError(VisualizationError):
    """A problem with encoding"""

    pass


class DrawElement:
    """An element is an operation that needs to be drawn."""

    def __init__(self, label=None):
        self._width = None
        self.label = self.mid_content = label
        self.top_format = self.mid_format = self.bot_format = "%s"
        self.top_connect = self.bot_connect = " "
        self.top_pad = self._mid_padding = self.bot_pad = " "
        self.mid_bck = self.top_bck = self.bot_bck = " "
        self.bot_connector = {}
        self.top_connector = {}
        self.right_fill = self.left_fill = self.layer_width = 0
        self.wire_label = ""

    @property
    def top(self):
        """Constructs the top line of the element"""
        if (self.width % 2) == 0 and len(self.top_format) % 2 == 1 and len(self.top_connect) == 1:
            ret = self.top_format % (self.top_pad + self.top_connect).center(
                self.width, self.top_pad
            )
        else:
            ret = self.top_format % self.top_connect.center(self.width, self.top_pad)
        if self.right_fill:
            ret = ret.ljust(self.right_fill, self.top_pad)
        if self.left_fill:
            ret = ret.rjust(self.left_fill, self.top_pad)
        ret = ret.center(self.layer_width, self.top_bck)
        return ret

    @property
    def mid(self):
        """Constructs the middle line of the element"""
        ret = self.mid_format % self.mid_content.center(self.width, self._mid_padding)
        if self.right_fill:
            ret = ret.ljust(self.right_fill, self._mid_padding)
        if self.left_fill:
            ret = ret.rjust(self.left_fill, self._mid_padding)
        ret = ret.center(self.layer_width, self.mid_bck)
        return ret

    @property
    def bot(self):
        """Constructs the bottom line of the element"""
        if (self.width % 2) == 0 and len(self.top_format) % 2 == 1:
            ret = self.bot_format % (self.bot_pad + self.bot_connect).center(
                self.width, self.bot_pad
            )
        else:
            ret = self.bot_format % self.bot_connect.center(self.width, self.bot_pad)
        if self.right_fill:
            ret = ret.ljust(self.right_fill, self.bot_pad)
        if self.left_fill:
            ret = ret.rjust(self.left_fill, self.bot_pad)
        ret = ret.center(self.layer_width, self.bot_bck)
        return ret

    @property
    def length(self):
        """Returns the length of the element, including the box around."""
        return max(len(self.top), len(self.mid), len(self.bot))

    @property
    def width(self):
        """Returns the width of the label, including padding"""
        if self._width:
            return self._width
        return len(self.mid_content)

    @width.setter
    def width(self, value):
        self._width = value

    def connect(self, wire_char, where, label=None):
        """Connects boxes and elements using wire_char and setting proper connectors.

        Args:
            wire_char (char): For example '║' or '│'.
            where (list["top", "bot"]): Where the connector should be set.
            label (string): Some connectors have a label (see cu1, for example).
        """

        if "top" in where and self.top_connector:
            self.top_connect = self.top_connector[wire_char]

        if "bot" in where and self.bot_connector:
            self.bot_connect = self.bot_connector[wire_char]

        if label:
            self.top_format = self.top_format[:-1] + (label if label else "")


class BoxOnClWire(DrawElement):
    """Draws a box on the classical wire.

    ::

        top: ┌───┐   ┌───┐
        mid: ╡ A ╞ ══╡ A ╞══
        bot: └───┘   └───┘
    """

    def __init__(self, label="", top_connect="─", bot_connect="─"):
        super().__init__(label)
        self.top_format = "┌─%s─┐"
        self.mid_format = "╡ %s ╞"
        self.bot_format = "└─%s─┘"
        self.top_pad = self.bot_pad = "─"
        self.mid_bck = "═"
        self.top_connect = top_connect
        self.bot_connect = bot_connect
        self.mid_content = label


class BoxOnQuWire(DrawElement):
    """Draws a box on the quantum wire.

    ::

        top: ┌───┐   ┌───┐
        mid: ┤ A ├ ──┤ A ├──
        bot: └───┘   └───┘
    """

    def __init__(self, label="", top_connect="─", conditional=False):
        super().__init__(label)
        self.top_format = "┌─%s─┐"
        self.mid_format = "┤ %s ├"
        self.bot_format = "└─%s─┘"
        self.top_pad = self.bot_pad = self.mid_bck = "─"
        self.top_connect = top_connect
        self.bot_connect = "╥" if conditional else "─"
        self.mid_content = label
        self.top_connector = {"│": "┴"}
        self.bot_connector = {"│": "┬"}


class MeasureTo(DrawElement):
    """The element on the classic wire to which the measure is performed.

    ::

        top:  ║     ║
        mid: ═╩═ ═══╩═══
        bot:
    """

    def __init__(self, label=""):
        super().__init__()
        self.top_connect = " ║ "
        self.mid_content = "═╩═"
        self.bot_connect = label
        self.mid_bck = "═"


class MeasureFrom(BoxOnQuWire):
    """The element on the quantum wire in which the measure is performed.

    ::

        top: ┌─┐    ┌─┐
        mid: ┤M├ ───┤M├───
        bot: └╥┘    └╥┘
    """

    def __init__(self):
        super().__init__()
        self.top_format = self.mid_format = self.bot_format = "%s"
        self.top_connect = "┌─┐"
        self.mid_content = "┤M├"
        self.bot_connect = "└╥┘"

        self.top_pad = self.bot_pad = " "
        self._mid_padding = "─"


class MultiBox(DrawElement):
    """Elements that are drawn over multiple wires."""

    def center_label(self, input_length, order):
        """In multi-bit elements, the label is centered vertically.

        Args:
            input_length (int): Rhe amount of wires affected.
            order (int): Which middle element is this one?
        """
        if input_length == order == 0:
            self.top_connect = self.label
            return
        location_in_the_box = "*".center(input_length * 2 - 1).index("*") + 1
        top_limit = order * 2 + 2
        bot_limit = top_limit + 2
        if top_limit <= location_in_the_box < bot_limit:
            if location_in_the_box == top_limit:
                self.top_connect = self.label
            elif location_in_the_box == top_limit + 1:
                self.mid_content = self.label
            else:
                self.bot_connect = self.label

    @property
    def width(self):
        """Returns the width of the label, including padding"""
        if self._width:
            return self._width
        return len(self.label)


class BoxOnQuWireTop(MultiBox, BoxOnQuWire):
    """Draws the top part of a box that affects more than one quantum wire"""

    def __init__(self, label="", top_connect=None, wire_label=""):
        super().__init__(label)
        self.wire_label = wire_label
        self.bot_connect = self.bot_pad = " "
        self.mid_content = ""  # The label will be put by some other part of the box.
        self.left_fill = len(self.wire_label)
        self.top_format = "┌─" + "s".center(self.left_fill + 1, "─") + "─┐"
        self.top_format = self.top_format.replace("s", "%s")
        self.mid_format = f"┤{self.wire_label} %s ├"
        self.bot_format = f"│{self.bot_pad * self.left_fill} %s │"
        self.top_connect = top_connect if top_connect else "─"


class BoxOnWireMid(MultiBox):
    """A generic middle box"""

    def __init__(self, label, input_length, order, wire_label=""):
        super().__init__(label)
        self.top_pad = self.bot_pad = self.top_connect = self.bot_connect = " "
        self.wire_label = wire_label
        self.left_fill = len(self.wire_label)
        self.top_format = f"│{self.top_pad * self.left_fill} %s │"
        self.bot_format = f"│{self.bot_pad * self.left_fill} %s │"
        self.top_connect = self.bot_connect = self.mid_content = ""
        self.center_label(input_length, order)


class BoxOnQuWireMid(BoxOnWireMid, BoxOnQuWire):
    """Draws the middle part of a box that affects more than one quantum wire"""

    def __init__(self, label, input_length, order, wire_label="", control_label=None):
        super().__init__(label, input_length, order, wire_label=wire_label)
        if control_label:
            self.mid_format = f"{control_label}{self.wire_label} %s ├"
        else:
            self.mid_format = f"┤{self.wire_label} %s ├"


class BoxOnQuWireBot(MultiBox, BoxOnQuWire):
    """Draws the bottom part of a box that affects more than one quantum wire"""

    def __init__(self, label, input_length, bot_connect=None, wire_label="", conditional=False):
        super().__init__(label)
        self.wire_label = wire_label
        self.top_pad = " "
        self.left_fill = len(self.wire_label)
        self.top_format = f"│{self.top_pad * self.left_fill} %s │"
        self.mid_format = f"┤{self.wire_label} %s ├"
        self.bot_format = "└─" + "s".center(self.left_fill + 1, "─") + "─┘"
        self.bot_format = self.bot_format.replace("s", "%s")
        bot_connect = bot_connect if bot_connect else "─"
        self.bot_connect = "╥" if conditional else bot_connect

        self.mid_content = self.top_connect = ""
        if input_length <= 2:
            self.top_connect = label


class BoxOnClWireTop(MultiBox, BoxOnClWire):
    """Draws the top part of a conditional box that affects more than one classical wire"""

    def __init__(self, label="", top_connect=None, wire_label=""):
        super().__init__(label)
        self.wire_label = wire_label
        self.mid_content = ""  # The label will be put by some other part of the box.
        self.bot_format = "│ %s │"
        self.top_connect = top_connect if top_connect else "─"
        self.bot_connect = self.bot_pad = " "


class BoxOnClWireMid(BoxOnWireMid, BoxOnClWire):
    """Draws the middle part of a conditional box that affects more than one classical wire"""

    def __init__(self, label, input_length, order, wire_label="", **_):
        super().__init__(label, input_length, order, wire_label=wire_label)
        self.mid_format = f"╡{self.wire_label} %s ╞"


class BoxOnClWireBot(MultiBox, BoxOnClWire):
    """Draws the bottom part of a conditional box that affects more than one classical wire"""

    def __init__(self, label, input_length, bot_connect="─", wire_label="", **_):
        super().__init__(label)
        self.wire_label = wire_label
        self.left_fill = len(self.wire_label)
        self.top_pad = " "
        self.bot_pad = "─"
        self.top_format = f"│{self.top_pad * self.left_fill} %s │"
        self.mid_format = f"╡{self.wire_label} %s ╞"
        self.bot_format = "└─" + "s".center(self.left_fill + 1, "─") + "─┘"
        self.bot_format = self.bot_format.replace("s", "%s")
        bot_connect = bot_connect if bot_connect else "─"
        self.bot_connect = bot_connect

        self.mid_content = self.top_connect = ""
        if input_length <= 2:
            self.top_connect = label


class DirectOnQuWire(DrawElement):
    """
    Element to the wire (without the box).
    """

    def __init__(self, label=""):
        super().__init__(label)
        self.top_format = " %s "
        self.mid_format = "─%s─"
        self.bot_format = " %s "
        self._mid_padding = self.mid_bck = "─"
        self.top_connector = {"│": "│"}
        self.bot_connector = {"│": "│"}


class Barrier(DirectOnQuWire):
    """Draws a barrier.

    ::

        top:  ░     ░
        mid: ─░─ ───░───
        bot:  ░     ░
    """

    def __init__(self, label=""):
        super().__init__("░")
        self.top_connect = "░"
        self.bot_connect = "░"
        self.top_connector = {}
        self.bot_connector = {}


class Ex(DirectOnQuWire):
    """Draws an X (usually with a connector). E.g. the top part of a swap gate.

    ::

        top:
        mid: ─X─ ───X───
        bot:  │     │
    """

    def __init__(self, bot_connect=" ", top_connect=" ", conditional=False):
        super().__init__("X")
        self.bot_connect = "║" if conditional else bot_connect
        self.top_connect = top_connect


class ResetDisplay(DirectOnQuWire):
    """Draws a reset gate"""

    def __init__(self, conditional=False):
        super().__init__("|0>")
        if conditional:
            self.bot_connect = "║"


class Bullet(DirectOnQuWire):
    """Draws a bullet (usually with a connector). E.g. the top part of a CX gate.

    ::

        top:
        mid: ─■─  ───■───
        bot:  │      │
    """

    def __init__(self, top_connect="", bot_connect="", conditional=False, label=None, bottom=False):
        super().__init__("■")
        self.top_connect = top_connect
        self.bot_connect = "║" if conditional else bot_connect
        if label and bottom:
            self.bot_connect = label
        elif label:
            self.top_connect = label
        self.mid_bck = "─"


class OpenBullet(DirectOnQuWire):
    """Draws an open bullet (usually with a connector). E.g. the top part of a CX gate.

    ::

        top:
        mid: ─o─  ───o───
        bot:  │      │
    """

    def __init__(self, top_connect="", bot_connect="", conditional=False, label=None, bottom=False):
        super().__init__("o")
        self.top_connect = top_connect
        self.bot_connect = "║" if conditional else bot_connect
        if label and bottom:
            self.bot_connect = label
        elif label:
            self.top_connect = label
        self.mid_bck = "─"


class DirectOnClWire(DrawElement):
    """
    Element to the classical wire (without the box).
    """

    def __init__(self, label=""):
        super().__init__(label)
        self.top_format = " %s "
        self.mid_format = "═%s═"
        self.bot_format = " %s "
        self._mid_padding = self.mid_bck = "═"
        self.top_connector = {"│": "│"}
        self.bot_connector = {"│": "│"}


class ClBullet(DirectOnClWire):
    """Draws a bullet on classical wire (usually with a connector). E.g. the top part of a CX gate.

    ::

        top:
        mid: ═■═  ═══■═══
        bot:  │      │
    """

    def __init__(self, top_connect="", bot_connect="", conditional=False, label=None, bottom=False):
        super().__init__("■")
        self.top_connect = top_connect
        self.bot_connect = "║" if conditional else bot_connect
        if label and bottom:
            self.bot_connect = label
        elif label:
            self.top_connect = label
        self.mid_bck = "═"


class ClOpenBullet(DirectOnClWire):
    """Draws an open bullet on classical wire (usually with a connector). E.g. the top part of a CX gate.

    ::

        top:
        mid: ═o═  ═══o═══
        bot:  │      │
    """

    def __init__(self, top_connect="", bot_connect="", conditional=False, label=None, bottom=False):
        super().__init__("o")
        self.top_connect = top_connect
        self.bot_connect = "║" if conditional else bot_connect
        if label and bottom:
            self.bot_connect = label
        elif label:
            self.top_connect = label
        self.mid_bck = "═"


class EmptyWire(DrawElement):
    """This element is just the wire, with no operations."""

    def __init__(self, wire):
        super().__init__(wire)
        self._mid_padding = self.mid_bck = wire

    @staticmethod
    def fillup_layer(layer, first_clbit):
        """Given a layer, replace the Nones in it with EmptyWire elements.

        Args:
            layer (list): The layer that contains Nones.
            first_clbit (int): The first wire that is classic.

        Returns:
            list: The new layer, with no Nones.
        """
        for nones in [i for i, x in enumerate(layer) if x is None]:
            layer[nones] = EmptyWire("═") if nones >= first_clbit else EmptyWire("─")
        return layer


class BreakWire(DrawElement):
    """This element is used to break the drawing in several pages."""

    def __init__(self, arrow_char):
        super().__init__()
        self.top_format = self.mid_format = self.bot_format = "%s"
        self.top_connect = arrow_char
        self.mid_content = arrow_char
        self.bot_connect = arrow_char

    @staticmethod
    def fillup_layer(layer_length, arrow_char):
        """Creates a layer with BreakWire elements.

        Args:
            layer_length (int): The length of the layer to create
            arrow_char (char): The char used to create the BreakWire element.

        Returns:
            list: The new layer.
        """
        breakwire_layer = []
        for _ in range(layer_length):
            breakwire_layer.append(BreakWire(arrow_char))
        return breakwire_layer


class InputWire(DrawElement):
    """This element is the label and the initial value of a wire."""

    def __init__(self, label):
        super().__init__(label)

    @staticmethod
    def fillup_layer(names):
        """Creates a layer with InputWire elements.

        Args:
            names (list): List of names for the wires.

        Returns:
            list: The new layer
        """
        longest = max(len(name) for name in names)
        inputs_wires = []
        for name in names:
            inputs_wires.append(InputWire(name.rjust(longest)))
        return inputs_wires


class TextDrawing:
    """The text drawing"""

    def __init__(
        self,
        qubits,
        clbits,
        nodes,
        reverse_bits=False,
        plotbarriers=True,
        line_length=None,
        vertical_compression="high",
        layout=None,
        initial_state=True,
        cregbundle=False,
        global_phase=None,
        encoding=None,
        qregs=None,
        cregs=None,
    ):
        self.qubits = qubits
        self.clbits = clbits
        self.qregs = qregs
        self.cregs = cregs
        self.nodes = nodes
        self.reverse_bits = reverse_bits
        self.layout = layout
        self.initial_state = initial_state
        self.cregbundle = cregbundle
        self.global_phase = global_phase
        self.plotbarriers = plotbarriers
        self.line_length = line_length
        if vertical_compression not in ["high", "medium", "low"]:
            raise ValueError("Vertical compression can only be 'high', 'medium', or 'low'")
        self.vertical_compression = vertical_compression

        if encoding:
            self.encoding = encoding
        else:
            if sys.stdout.encoding:
                self.encoding = sys.stdout.encoding
            else:
                self.encoding = "utf8"

        self.bit_locations = {
            bit: {"register": register, "index": index}
            for register in cregs + qregs
            for index, bit in enumerate(register)
        }
        for index, bit in list(enumerate(qubits)) + list(enumerate(clbits)):
            if bit not in self.bit_locations:
                self.bit_locations[bit] = {"register": None, "index": index}

    def __str__(self):
        return self.single_string()

    def _repr_html_(self):
        return (
            '<pre style="word-wrap: normal;'
            "white-space: pre;"
            "background: #fff0;"
            "line-height: 1.1;"
            'font-family: &quot;Courier New&quot;,Courier,monospace">'
            "%s</pre>" % self.single_string()
        )

    def __repr__(self):
        return self.single_string()

    def single_string(self):
        """Creates a long string with the ascii art.
        Returns:
            str: The lines joined by a newline (``\\n``)
        """
        try:
            return "\n".join(self.lines()).encode(self.encoding).decode(self.encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            warn(
                "The encoding %s has a limited charset. Consider a different encoding in your "
                "environment. UTF-8 is being used instead" % self.encoding,
                RuntimeWarning,
            )
            self.encoding = "utf-8"
            return "\n".join(self.lines()).encode(self.encoding).decode(self.encoding)

    def dump(self, filename, encoding=None):
        """Dumps the ascii art in the file.

        Args:
            filename (str): File to dump the ascii art.
            encoding (str): Optional. Force encoding, instead of self.encoding.
        """
        with open(filename, mode="w", encoding=encoding or self.encoding) as text_file:
            text_file.write(self.single_string())

    def lines(self, line_length=None):
        """Generates a list with lines. These lines form the text drawing.

        Args:
            line_length (int): Optional. Breaks the circuit drawing to this length. This is
                               useful when the drawing does not fit in the console. If
                               None (default), it will try to guess the console width using
                               shutil.get_terminal_size(). If you don't want pagination
                               at all, set line_length=-1.

        Returns:
            list: A list of lines with the text drawing.
        """
        if line_length is None:
            line_length = self.line_length
        if not line_length:
            if ("ipykernel" in sys.modules) and ("spyder" not in sys.modules):
                line_length = 80
            else:
                line_length, _ = get_terminal_size()

        noqubits = len(self.qubits)

        try:
            layers = self.build_layers()
        except TextDrawerCregBundle:
            self.cregbundle = False
            warn(
                'The parameter "cregbundle" was disabled, since an instruction needs to refer to '
                "individual classical wires",
                RuntimeWarning,
                2,
            )
            layers = self.build_layers()

        layer_groups = [[]]
        rest_of_the_line = line_length
        for layerno, layer in enumerate(layers):
            # Replace the Nones with EmptyWire
            layers[layerno] = EmptyWire.fillup_layer(layer, noqubits)

            TextDrawing.normalize_width(layer)

            if line_length == -1:
                # Do not use pagination (aka line breaking. aka ignore line_length).
                layer_groups[-1].append(layer)
                continue

            # chop the layer to the line_length (pager)
            layer_length = layers[layerno][0].length

            if layer_length < rest_of_the_line:
                layer_groups[-1].append(layer)
                rest_of_the_line -= layer_length
            else:
                layer_groups[-1].append(BreakWire.fillup_layer(len(layer), "»"))

                # New group
                layer_groups.append([BreakWire.fillup_layer(len(layer), "«")])
                rest_of_the_line = line_length - layer_groups[-1][-1][0].length

                layer_groups[-1].append(
                    InputWire.fillup_layer(self.wire_names(with_initial_state=False))
                )
                rest_of_the_line -= layer_groups[-1][-1][0].length

                layer_groups[-1].append(layer)
                rest_of_the_line -= layer_groups[-1][-1][0].length

        lines = []

        if self.global_phase:
            lines.append("global phase: %s" % pi_check(self.global_phase, ndigits=5))

        for layer_group in layer_groups:
            wires = list(zip(*layer_group))
            lines += self.draw_wires(wires)

        return lines

    def wire_names(self, with_initial_state=False):
        """Returns a list of names for each wire.

        Args:
            with_initial_state (bool): Optional (Default: False). If true, adds
                the initial value to the name.

        Returns:
            List: The list of wire names.
        """
        if with_initial_state:
            initial_qubit_value = "|0>"
            initial_clbit_value = "0 "
        else:
            initial_qubit_value = ""
            initial_clbit_value = ""

        # quantum register
        qubit_labels = []
        for reg in self.qubits:
            register = self.bit_locations[reg]["register"]
            index = self.bit_locations[reg]["index"]
            qubit_label = get_bit_label("text", register, index, qubit=True, layout=self.layout)
            qubit_label += ": " if self.layout is None else " "
            qubit_labels.append(qubit_label + initial_qubit_value)

        # classical register
        clbit_labels = []
        if self.clbits:
            prev_creg = None
            for reg in self.clbits:
                register = self.bit_locations[reg]["register"]
                index = self.bit_locations[reg]["index"]
                clbit_label = get_bit_label(
                    "text", register, index, qubit=False, cregbundle=self.cregbundle
                )
                if register is None or not self.cregbundle or prev_creg != register:
                    cregb_add = (
                        str(register.size) + "/" if self.cregbundle and register is not None else ""
                    )
                    clbit_labels.append(clbit_label + ": " + initial_clbit_value + cregb_add)
                prev_creg = register

        return qubit_labels + clbit_labels

    def should_compress(self, top_line, bot_line):
        """Decides if the top_line and bot_line should be merged,
        based on `self.vertical_compression`."""
        if self.vertical_compression == "high":
            return True
        if self.vertical_compression == "low":
            return False
        for top, bot in zip(top_line, bot_line):
            if top in ["┴", "╨"] and bot in ["┬", "╥"]:
                return False
        for line in (bot_line, top_line):
            no_spaces = line.replace(" ", "")
            if len(no_spaces) > 0 and all(c.isalpha() or c.isnumeric() for c in no_spaces):
                return False
        return True

    def draw_wires(self, wires):
        """Given a list of wires, creates a list of lines with the text drawing.

        Args:
            wires (list): A list of wires with nodes.
        Returns:
            list: A list of lines with the text drawing.
        """
        lines = []
        bot_line = None
        for wire in wires:
            # TOP
            top_line = ""
            for node in wire:
                top_line += node.top

            if bot_line is None:
                lines.append(top_line)
            else:
                if self.should_compress(top_line, bot_line):
                    lines.append(TextDrawing.merge_lines(lines.pop(), top_line))
                else:
                    lines.append(TextDrawing.merge_lines(lines[-1], top_line, icod="bot"))

            # MID
            mid_line = ""
            for node in wire:
                mid_line += node.mid
            lines.append(TextDrawing.merge_lines(lines[-1], mid_line, icod="bot"))

            # BOT
            bot_line = ""
            for node in wire:
                bot_line += node.bot
            lines.append(TextDrawing.merge_lines(lines[-1], bot_line, icod="bot"))

        return lines

    @staticmethod
    def special_label(node):
        """Some instructions have special labels"""
        labels = {IGate: "I", SXGate: "√X", SXdgGate: "√Xdg"}
        node_type = type(node)
        return labels.get(node_type, None)

    @staticmethod
    def merge_lines(top, bot, icod="top"):
        """Merges two lines (top and bot) in a way that the overlapping makes sense.

        Args:
            top (str): the top line
            bot (str): the bottom line
            icod (top or bot): in case of doubt, which line should have priority? Default: "top".
        Returns:
            str: The merge of both lines.
        """
        ret = ""
        for topc, botc in zip(top, bot):
            if topc == botc:
                ret += topc
            elif topc in "┼╪" and botc == " ":
                ret += "│"
            elif topc == " ":
                ret += botc
            elif topc in "┬╥" and botc in " ║│" and icod == "top":
                ret += topc
            elif topc in "┬" and botc == " " and icod == "bot":
                ret += "│"
            elif topc in "╥" and botc == " " and icod == "bot":
                ret += "║"
            elif topc in "┬│" and botc == "═":
                ret += "╪"
            elif topc in "┬│" and botc == "─":
                ret += "┼"
            elif topc in "└┘║│░" and botc == " " and icod == "top":
                ret += topc
            elif topc in "─═" and botc == " " and icod == "top":
                ret += topc
            elif topc in "─═" and botc == " " and icod == "bot":
                ret += botc
            elif topc in "║╥" and botc in "═":
                ret += "╬"
            elif topc in "║╥" and botc in "─":
                ret += "╫"
            elif topc in "║╫╬" and botc in " ":
                ret += "║"
            elif topc == "└" and botc == "┌" and icod == "top":
                ret += "├"
            elif topc == "┘" and botc == "┐":
                ret += "┤"
            elif botc in "┐┌" and icod == "top":
                ret += "┬"
            elif topc in "┘└" and botc in "─" and icod == "top":
                ret += "┴"
            elif botc == " " and icod == "top":
                ret += topc
            else:
                ret += botc
        return ret

    @staticmethod
    def normalize_width(layer):
        """
        When the elements of the layer have different widths, sets the width to the max elements.

        Args:
            layer (list): A list of elements.
        """
        nodes = list(filter(lambda x: x is not None, layer))
        longest = max(node.length for node in nodes)
        for node in nodes:
            node.layer_width = longest

    @staticmethod
    def controlled_wires(node, layer):
        """
        Analyzes the node in the layer and checks if the controlled arguments are in
        the box or out of the box.

        Args:
            node (DAGNode): node to analyse
            layer (Layer): The layer in which the node is inserted.

        Returns:
            Tuple(list, list, list):
              - tuple: controlled arguments on top of the "node box", and its status
              - tuple: controlled arguments on bottom of the "node box", and its status
              - tuple: controlled arguments in the "node box", and its status
              - the rest of the arguments
        """
        op = node.op
        num_ctrl_qubits = op.num_ctrl_qubits
        ctrl_qubits = node.qargs[:num_ctrl_qubits]
        args_qubits = node.qargs[num_ctrl_qubits:]
        ctrl_state = f"{op.ctrl_state:b}".rjust(num_ctrl_qubits, "0")[::-1]

        in_box = []
        top_box = []
        bot_box = []

        qubit_index = sorted(i for i, x in enumerate(layer.qubits) if x in args_qubits)

        for ctrl_qubit in zip(ctrl_qubits, ctrl_state):
            if min(qubit_index) > layer.qubits.index(ctrl_qubit[0]):
                top_box.append(ctrl_qubit)
            elif max(qubit_index) < layer.qubits.index(ctrl_qubit[0]):
                bot_box.append(ctrl_qubit)
            else:
                in_box.append(ctrl_qubit)
        return (top_box, bot_box, in_box, args_qubits)

    def _set_ctrl_state(self, node, conditional, ctrl_text, bottom):
        """Takes the ctrl_state from node.op and appends Bullet or OpenBullet
        to gates depending on whether the bit in ctrl_state is 1 or 0. Returns gates"""
        op = node.op
        gates = []
        num_ctrl_qubits = op.num_ctrl_qubits
        ctrl_qubits = node.qargs[:num_ctrl_qubits]
        cstate = f"{op.ctrl_state:b}".rjust(num_ctrl_qubits, "0")[::-1]
        for i in range(len(ctrl_qubits)):
            if cstate[i] == "1":
                gates.append(Bullet(conditional=conditional, label=ctrl_text, bottom=bottom))
            else:
                gates.append(OpenBullet(conditional=conditional, label=ctrl_text, bottom=bottom))
        return gates

    def _node_to_gate(self, node, layer):
        """Convert a dag op node into its corresponding Gate object, and establish
        any connections it introduces between qubits"""
        op = node.op
        current_cons = []
        connection_label = None
        conditional = False
        base_gate = getattr(op, "base_gate", None)

        params = get_param_str(op, "text", ndigits=5)
        if not isinstance(op, (Measure, SwapGate, Reset)) and not op._directive:
            gate_text, ctrl_text, _ = get_gate_ctrl_text(op, "text")
            gate_text = TextDrawing.special_label(op) or gate_text
            gate_text = gate_text + params

        if op.condition is not None:
            # conditional
            op_cond = op.condition
            layer.set_cl_multibox(op_cond[0], op_cond[1], top_connect="╨")
            conditional = True

        # add in a gate that operates over multiple qubits
        def add_connected_gate(node, gates, layer, current_cons):
            for i, gate in enumerate(gates):
                actual_index = self.qubits.index(node.qargs[i])
                if actual_index not in [i for i, j in current_cons]:
                    layer.set_qubit(node.qargs[i], gate)
                    current_cons.append((actual_index, gate))

        if isinstance(op, Measure):
            gate = MeasureFrom()
            layer.set_qubit(node.qargs[0], gate)
            if self.cregbundle:
                layer.set_clbit(
                    node.cargs[0],
                    MeasureTo(str(self.bit_locations[node.cargs[0]]["index"])),
                )
            else:
                layer.set_clbit(node.cargs[0], MeasureTo())

        elif op._directive:
            # barrier
            if not self.plotbarriers:
                return layer, current_cons, connection_label

            for qubit in node.qargs:
                if qubit in self.qubits:
                    layer.set_qubit(qubit, Barrier())

        elif isinstance(op, SwapGate):
            # swap
            gates = [Ex(conditional=conditional) for _ in range(len(node.qargs))]
            add_connected_gate(node, gates, layer, current_cons)

        elif isinstance(op, Reset):
            # reset
            layer.set_qubit(node.qargs[0], ResetDisplay(conditional=conditional))

        elif isinstance(op, RZZGate):
            # rzz
            connection_label = "ZZ%s" % params
            gates = [Bullet(conditional=conditional), Bullet(conditional=conditional)]
            add_connected_gate(node, gates, layer, current_cons)

        elif len(node.qargs) == 1 and not node.cargs:
            # unitary gate
            layer.set_qubit(node.qargs[0], BoxOnQuWire(gate_text, conditional=conditional))

        elif isinstance(op, ControlledGate):
            params_array = TextDrawing.controlled_wires(node, layer)
            controlled_top, controlled_bot, controlled_edge, rest = params_array
            gates = self._set_ctrl_state(node, conditional, ctrl_text, bool(controlled_bot))
            if base_gate.name == "z":
                # cz
                gates.append(Bullet(conditional=conditional))
            elif base_gate.name in ["u1", "p"]:
                # cu1
                connection_label = f"{base_gate.name.upper()}{params}"
                gates.append(Bullet(conditional=conditional))
            elif base_gate.name == "swap":
                # cswap
                gates += [Ex(conditional=conditional), Ex(conditional=conditional)]
                add_connected_gate(node, gates, layer, current_cons)
            elif base_gate.name == "rzz":
                # crzz
                connection_label = "ZZ%s" % params
                gates += [Bullet(conditional=conditional), Bullet(conditional=conditional)]
            elif len(rest) > 1:
                top_connect = "┴" if controlled_top else None
                bot_connect = "┬" if controlled_bot else None
                indexes = layer.set_qu_multibox(
                    rest,
                    gate_text,
                    conditional=conditional,
                    controlled_edge=controlled_edge,
                    top_connect=top_connect,
                    bot_connect=bot_connect,
                )
                for index in range(min(indexes), max(indexes) + 1):
                    # Dummy element to connect the multibox with the bullets
                    current_cons.append((index, DrawElement("")))
            else:
                gates.append(BoxOnQuWire(gate_text, conditional=conditional))
            add_connected_gate(node, gates, layer, current_cons)

        elif len(node.qargs) >= 2 and not node.cargs:
            layer.set_qu_multibox(node.qargs, gate_text, conditional=conditional)

        elif node.qargs and node.cargs:
            if self.cregbundle and node.cargs:
                raise TextDrawerCregBundle("TODO")
            layer._set_multibox(
                gate_text,
                qubits=node.qargs,
                clbits=node.cargs,
                conditional=conditional,
            )
        else:
            raise VisualizationError(
                "Text visualizer does not know how to handle this node: ", op.name
            )

        # sort into the order they were declared in, to ensure that connected boxes have
        # lines in the right direction
        current_cons.sort(key=lambda tup: tup[0])
        current_cons = [g for q, g in current_cons]

        return layer, current_cons, connection_label

    def build_layers(self):
        """
        Constructs layers.
        Returns:
            list: List of DrawElements.
        Raises:
            VisualizationError: When the drawing is, for some reason, impossible to be drawn.
        """
        wire_names = self.wire_names(with_initial_state=self.initial_state)
        if not wire_names:
            return []

        layers = [InputWire.fillup_layer(wire_names)]

        for node_layer in self.nodes:
            layer = Layer(self.qubits, self.clbits, self.reverse_bits, self.cregbundle, self.cregs)

            for node in node_layer:
                layer, current_connections, connection_label = self._node_to_gate(node, layer)

                layer.connections.append((connection_label, current_connections))
            layer.connect_with("│")
            layers.append(layer.full_layer)

        return layers


class Layer:
    """A layer is the "column" of the circuit."""

    def __init__(self, qubits, clbits, reverse_bits=False, cregbundle=False, cregs=None):
        cregs = [] if cregs is None else cregs

        self.qubits = qubits

        self._clbit_locations = {
            bit: {"register": register, "index": index}
            for register in cregs
            for index, bit in enumerate(register)
        }
        for index, bit in enumerate(clbits):
            if bit not in self._clbit_locations:
                self._clbit_locations[bit] = {"register": None, "index": index}

        if cregbundle:
            self.clbits = []
            previous_creg = None
            for bit in clbits:
                if previous_creg and previous_creg == self._clbit_locations[bit]["register"]:
                    continue
                previous_creg = self._clbit_locations[bit]["register"]
                self.clbits.append(previous_creg)
        else:
            self.clbits = clbits
        self.qubit_layer = [None] * len(qubits)
        self.connections = []
        self.clbit_layer = [None] * len(clbits)
        self.reverse_bits = reverse_bits
        self.cregbundle = cregbundle

    @property
    def full_layer(self):
        """
        Returns the composition of qubits and classic wires.
        Returns:
            String: self.qubit_layer + self.clbit_layer
        """
        return self.qubit_layer + self.clbit_layer

    def set_qubit(self, qubit, element):
        """Sets the qubit to the element.

        Args:
            qubit (qbit): Element of self.qubits.
            element (DrawElement): Element to set in the qubit
        """
        self.qubit_layer[self.qubits.index(qubit)] = element

    def set_clbit(self, clbit, element):
        """Sets the clbit to the element.

        Args:
            clbit (cbit): Element of self.clbits.
            element (DrawElement): Element to set in the clbit
        """
        if self.cregbundle:
            self.clbit_layer[self.clbits.index(self._clbit_locations[clbit]["register"])] = element
        else:
            self.clbit_layer[self.clbits.index(clbit)] = element

    def _set_multibox(
        self,
        label,
        qubits=None,
        clbits=None,
        top_connect=None,
        bot_connect=None,
        conditional=False,
        controlled_edge=None,
    ):
        if qubits is not None and clbits is not None:
            cbit_index = sorted(i for i, x in enumerate(self.clbits) if x in clbits)
            qbit_index = sorted(i for i, x in enumerate(self.qubits) if x in qubits)

            # Further below, indices are used as wire labels. Here, get the length of
            # the longest label, and pad all labels with spaces to this length.
            wire_label_len = max(len(str(len(qubits) - 1)), len(str(len(clbits) - 1)))
            qargs = [
                str(qubits.index(qbit)).ljust(wire_label_len, " ")
                for qbit in self.qubits
                if qbit in qubits
            ]
            cargs = [
                str(clbits.index(cbit)).ljust(wire_label_len, " ")
                for cbit in self.clbits
                if cbit in clbits
            ]

            qubits = sorted(qubits, key=self.qubits.index)
            clbits = sorted(clbits, key=self.clbits.index)

            box_height = len(self.qubits) - min(qbit_index) + max(cbit_index) + 1

            self.set_qubit(qubits.pop(0), BoxOnQuWireTop(label, wire_label=qargs.pop(0)))
            order = 0
            for order, bit_i in enumerate(range(min(qbit_index) + 1, len(self.qubits))):
                if bit_i in qbit_index:
                    named_bit = qubits.pop(0)
                    wire_label = qargs.pop(0)
                else:
                    named_bit = self.qubits[bit_i]
                    wire_label = " " * wire_label_len
                self.set_qubit(
                    named_bit, BoxOnQuWireMid(label, box_height, order, wire_label=wire_label)
                )
            for order, bit_i in enumerate(range(max(cbit_index)), order + 1):
                if bit_i in cbit_index:
                    named_bit = clbits.pop(0)
                    wire_label = cargs.pop(0)
                else:
                    named_bit = self.clbits[bit_i]
                    wire_label = " " * wire_label_len
                self.set_clbit(
                    named_bit, BoxOnClWireMid(label, box_height, order, wire_label=wire_label)
                )
            self.set_clbit(
                clbits.pop(0), BoxOnClWireBot(label, box_height, wire_label=cargs.pop(0))
            )
            return cbit_index
        if qubits is None and clbits is not None:
            bits = list(clbits)
            bit_index = sorted(i for i, x in enumerate(self.clbits) if x in bits)
            wire_label_len = len(str(len(bits) - 1))
            bits.sort(key=self.clbits.index)
            qargs = [""] * len(bits)
            set_bit = self.set_clbit
            OnWire = BoxOnClWire
            OnWireTop = BoxOnClWireTop
            OnWireMid = BoxOnClWireMid
            OnWireBot = BoxOnClWireBot
        elif clbits is None and qubits is not None:
            bits = list(qubits)
            bit_index = sorted(i for i, x in enumerate(self.qubits) if x in bits)
            wire_label_len = len(str(len(bits) - 1))
            qargs = [
                str(bits.index(qbit)).ljust(wire_label_len, " ")
                for qbit in self.qubits
                if qbit in bits
            ]
            bits.sort(key=self.qubits.index)
            set_bit = self.set_qubit
            OnWire = BoxOnQuWire
            OnWireTop = BoxOnQuWireTop
            OnWireMid = BoxOnQuWireMid
            OnWireBot = BoxOnQuWireBot
        else:
            raise VisualizationError("_set_multibox error!.")

        control_index = {}
        if controlled_edge:
            for index, qubit in enumerate(self.qubits):
                for qubit_in_edge, value in controlled_edge:
                    if qubit == qubit_in_edge:
                        control_index[index] = "■" if value == "1" else "o"
        if len(bit_index) == 1:
            set_bit(bits[0], OnWire(label, top_connect=top_connect))
        else:
            box_height = max(bit_index) - min(bit_index) + 1
            set_bit(bits.pop(0), OnWireTop(label, top_connect=top_connect, wire_label=qargs.pop(0)))
            for order, bit_i in enumerate(range(min(bit_index) + 1, max(bit_index))):
                if bit_i in bit_index:
                    named_bit = bits.pop(0)
                    wire_label = qargs.pop(0)
                else:
                    named_bit = (self.qubits + self.clbits)[bit_i]
                    wire_label = " " * wire_label_len

                control_label = control_index.get(bit_i)
                set_bit(
                    named_bit,
                    OnWireMid(
                        label, box_height, order, wire_label=wire_label, control_label=control_label
                    ),
                )
            set_bit(
                bits.pop(0),
                OnWireBot(
                    label,
                    box_height,
                    bot_connect=bot_connect,
                    wire_label=qargs.pop(0),
                    conditional=conditional,
                ),
            )
        return bit_index

    def set_cl_multibox(self, creg, val, top_connect="┴"):
        """Sets the multi clbit box.

        Args:
            creg (string): The affected classical register.
            val (int): The value of the condition.
            top_connect (char): The char to connect the box on the top.
        """
        if self.cregbundle:
            if isinstance(creg, Clbit):
                bit_reg = self._clbit_locations[creg]["register"]
                bit_index = self._clbit_locations[creg]["index"]
                label_bool = "= T" if val is True else "= F"
                label = f"{bit_reg.name}_{bit_index} {label_bool}"
                self.set_clbit(creg, BoxOnClWire(label=label, top_connect=top_connect))
            else:
                label = "%s" % str(hex(val))
                self.set_clbit(creg[0], BoxOnClWire(label=label, top_connect=top_connect))
        else:
            if isinstance(creg, Clbit):
                clbit = [creg]
                cond_bin = "1" if val is True else "0"
                self.set_cond_bullets(cond_bin, clbit)
            else:
                clbit = [
                    bit for bit in self.clbits if self._clbit_locations[bit]["register"] == creg
                ]
                cond_bin = bin(val)[2:].zfill(len(clbit))
                self.set_cond_bullets(cond_bin, clbits=clbit)

    def set_cond_bullets(self, val, clbits):
        """Sets bullets for classical conditioning when cregbundle=False.

        Args:
            val (int): The condition value.
            clbits (list[Clbit]): The list of classical bits on
                which the instruction is conditioned.
        """
        vlist = list(val) if self.reverse_bits else list(val[::-1])
        for i, bit in enumerate(clbits):
            bot_connect = " "
            if bit == clbits[-1]:
                bot_connect = "%s" % str(hex(int(val, 2)))
            if vlist[i] == "1":
                self.set_clbit(bit, ClBullet(top_connect="║", bot_connect=bot_connect))
            elif vlist[i] == "0":
                self.set_clbit(bit, ClOpenBullet(top_connect="║", bot_connect=bot_connect))

    def set_qu_multibox(
        self,
        bits,
        label,
        top_connect=None,
        bot_connect=None,
        conditional=False,
        controlled_edge=None,
    ):
        """Sets the multi qubit box.

        Args:
            bits (list[int]): A list of affected bits.
            label (string): The label for the multi qubit box.
            top_connect (char): None or a char connector on the top
            bot_connect (char): None or a char connector on the bottom
            conditional (bool): If the box has a conditional
            controlled_edge (list): A list of bit that are controlled (to draw them at the edge)
        Return:
            List: A list of indexes of the box.
        """
        return self._set_multibox(
            label,
            qubits=bits,
            top_connect=top_connect,
            bot_connect=bot_connect,
            conditional=conditional,
            controlled_edge=controlled_edge,
        )

    def connect_with(self, wire_char):
        """Connects the elements in the layer using wire_char.

        Args:
            wire_char (char): For example '║' or '│'.
        """

        if len([qbit for qbit in self.qubit_layer if qbit is not None]) == 1:
            # Nothing to connect
            return

        for label, affected_bits in self.connections:

            if not affected_bits:
                continue

            affected_bits[0].connect(wire_char, ["bot"])
            for affected_bit in affected_bits[1:-1]:
                affected_bit.connect(wire_char, ["bot", "top"])

            affected_bits[-1].connect(wire_char, ["top"], label)

            if label:
                for affected_bit in affected_bits:
                    affected_bit.right_fill = len(label) + len(affected_bit.mid)
