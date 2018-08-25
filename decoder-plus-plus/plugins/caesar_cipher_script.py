import math
import string

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIntValidator
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit, QFrame, QPlainTextEdit, QShortcut, \
    QSlider, QHBoxLayout, QPushButton

from core.exception import AbortedException
from core.plugin.plugin import ScriptPlugin

class Plugin(ScriptPlugin):
    """
    Opens a dialog to transform text using caesar-cipher.
    """

    def __init__(self, context):
        # Name, Author, Dependencies
        super().__init__('Caesar Cipher', "Thomas Engel", )
        self._shift = None
        self._dialog = None

    def select(self, text):
        if not self._dialog:
            self._dialog = CaesarCipherDialog(text, self._do_caesar)
        else:
            self._dialog.setInput(text)

        if self._dialog.exec_() == QDialog.Accepted:
            self._shift = self._dialog.getShift()
            return self.run(text)
        else:
            # User clicked the Cancel-Button.
            self._shift = None
            raise AbortedException("Aborted")

    def title(self):
        return "{} shift {}".format("Caesar Cipher", self._shift)

    def run(self, text, shift=None):
        return self._do_caesar(text, self._shift)

    def _do_caesar(self, plaintext, shift):
        alphabet = string.ascii_lowercase
        shifted_alphabet = alphabet[shift:] + alphabet[:shift]
        table = str.maketrans(alphabet, shifted_alphabet)
        return plaintext.translate(table)


class CaesarCipherOffsetCalculator:
    """
    Calculates the offset of a Caesar Cipher based on known frequency of English letters.
    Based on code from RobSpectre (see https://github.com/RobSpectre/Caesar-Cipher/)
    """

    def __init__(self):
        # Frequency of letters used in English, taken from Wikipedia.
        # http://en.wikipedia.org/wiki/Letter_frequency
        self.frequency = {
            'a': 0.08167,
            'b': 0.01492,
            'c': 0.02782,
            'd': 0.04253,
            'e': 0.130001,
            'f': 0.02228,
            'g': 0.02015,
            'h': 0.06094,
            'i': 0.06966,
            'j': 0.00153,
            'k': 0.00772,
            'l': 0.04025,
            'm': 0.02406,
            'n': 0.06749,
            'o': 0.07507,
            'p': 0.01929,
            'q': 0.00095,
            'r': 0.05987,
            's': 0.06327,
            't': 0.09056,
            'u': 0.02758,
            'v': 0.00978,
            'w': 0.02360,
            'x': 0.00150,
            'y': 0.01974,
            'z': 0.00074}

    def _calculate_entropy(self, input):
        """
        Calculates the entropy of a string based on known frequency.
        :param input: the input string.
        :return: a negative float with the total entropy of the input (higher is better).
        """
        total = 0
        for char in input:
            if char.isalpha():
                prob = self.frequency[char.lower()]
                total += - math.log(prob) / math.log(2)
        return total

    def _cipher(self, input, offset):
        """
        Applies the caesar cipher.
        :param input: the input string.
        :param offset: integer by which the value of the letters should be shifted.
        :return: String with cipher applied.
        """
        alphabet = string.ascii_lowercase
        shifted_alphabet = alphabet[offset:] + alphabet[:offset]
        table = str.maketrans(alphabet, shifted_alphabet)
        return input.translate(table)

    def calculate_offset(self, input):
        """
        Attempts to calculate offset of ciphertext using frequency of letters in English.
        :param input: the input string.
        :return: the most likely offset
        """
        entropy_values = {}
        for i in range(25):
            offset = i * -1
            test_cipher = self._cipher(input, offset)
            entropy_values[i] = self._calculate_entropy(test_cipher)

        sorted_by_entropy = sorted(entropy_values, key=entropy_values.get)
        offset = sorted_by_entropy[0] * -1
        return abs(offset)


class CaesarCipherDialog(QDialog):

    def __init__(self, input, callback):
        super(CaesarCipherDialog, self).__init__()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self._init_editor_frame())
        main_layout.addWidget(self._init_button_box())
        self.setLayout(main_layout)
        self.setWindowIcon(qtawesome.icon("fa.edit"))
        self.setWindowTitle("Caesar Cipher")
        self._setup_shortcuts()
        self._input = input
        self._text_area.setPlainText(self._input)
        self._callback = callback
        self._offset_calculator = CaesarCipherOffsetCalculator()


    def _setup_shortcuts(self):
        ctrl_return_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return), self)
        ctrl_return_shortcut.activated.connect(self._accept)
        alt_return_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Return), self)
        alt_return_shortcut.activated.connect(self._accept)
        alt_o_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_O), self)
        alt_o_shortcut.activated.connect(self._accept)

    def _init_button_box(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        return button_box

    def _init_editor_frame(self):
        main_frame = QFrame()
        main_frame_layout = QVBoxLayout()

        slider_frame = self._init_slider_frame()
        main_frame_layout.addWidget(slider_frame)

        self._text_area = QPlainTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setFixedHeight(126)
        main_frame_layout.addWidget(self._text_area)

        main_frame.setLayout(main_frame_layout)
        return main_frame

    def _init_slider_frame(self):
        slider_frame = QFrame()
        slider_frame_layout = QHBoxLayout()

        self._shift_slider = QSlider(Qt.Horizontal)
        self._shift_slider.setMinimum(0)
        self._shift_slider.setMaximum(26)
        self._shift_slider.setValue(0)
        self._shift_slider.valueChanged.connect(self._shift_slider_changed)
        slider_frame_layout.addWidget(self._shift_slider)

        self._shift_text = QLineEdit()
        self._shift_text.setText("0")
        self._shift_text.setFixedWidth(30)
        self._shift_text.setValidator(QIntValidator(0, 26))
        self._shift_text.textChanged.connect(self._shift_text_changed)
        slider_frame_layout.addWidget(self._shift_text)

        self._shift_calculate_button = QPushButton("Calculate")
        self._shift_calculate_button.clicked.connect(self._shift_calculate_button_clicked)
        slider_frame_layout.addWidget(self._shift_calculate_button)

        slider_frame.setLayout(slider_frame_layout)
        return slider_frame

    def _shift_calculate_button_clicked(self):
        offset = self._offset_calculator.calculate_offset(self._input)
        self._shift_slider.setSliderPosition(offset)

    def _shift_slider_changed(self, shift):
        if not shift:
            shift = 0
        self._shift_changed(shift)

    def _shift_text_changed(self, shift):
        if not shift:
            shift = 0
        self._shift_changed(int(shift))

    def _shift_changed(self, shift):
        self._shift_text.blockSignals(True)
        self._shift_slider.blockSignals(True)
        self._shift_slider.setValue(shift)
        self._shift_text.setText(str(shift))
        self._text_area.setPlainText(self._callback(self._input, shift))
        self._shift_slider.blockSignals(False)
        self._shift_text.blockSignals(False)

    def _accept(self):
        self.accept()

    def setInput(self, input):
        self._input = input
        self._shift_changed(self.getShift())

    def getShift(self):
        return self._shift_slider.value()
