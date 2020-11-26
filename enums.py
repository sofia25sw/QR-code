from enum import Enum


class EncodingMethod(Enum):
    ONLY_DIGIT = '0001'
    LETTER_DIGIT = '0010'
    BYTECODE = '0100'
