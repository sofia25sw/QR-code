from re import fullmatch

from exceptions import *
from utils import *
from enums import *


class Generator:

    def __init__(self, *, correction_level='M', encoding='utf-8'):
        if correction_level not in CORRECTION_LEVELS:
            raise ConfigurationException(f'Уровень коррекции задан неверно. Допустимые значения: {CORRECTION_LEVELS}')
        if encoding not in ALLOWED_ENCODINGS:
            raise ConfigurationException(f'Кодировка указана неверно. Допустимые значения: {ALLOWED_ENCODINGS}')

        # Correction level
        self.CL = correction_level
        self.encoding = encoding


    @staticmethod
    def __define_method(str_to_define: str) -> EncodingMethod:
        """
        Определяет метод кодирования
        :param str_to_define: Строка для кодирования
        :return: Метод из перечисления EncodingMethod
        """
        if fullmatch(ONLY_DIGIT_REGEXP, str_to_define):
            return EncodingMethod.ONLY_DIGIT
        if fullmatch(LETTER_DIGIT_REGEXP, str_to_define):
            return EncodingMethod.LETTER_DIGIT
        return EncodingMethod.BYTECODE


    @staticmethod
    def int_to_bin(number: int, addition: int = 0) -> str:
        b = bin(number).lstrip('0b')
        if addition:
            b = '0' * (addition - len(b)) + b
        return b


    def __encode_only_digit(self, str_to_encode: str) -> str:
        """
        Кодирует цифровую строку
        :param str_to_encode: Строка для кодирования
        :return: Побитово закодированная строка
        """
        groups = [str_to_encode[i * 3: (i + 1) * 3] for i in range(len(str_to_encode) // 3)]
        groups = list(map(lambda x: Generator.int_to_bin(int(x), 10), groups))
        if mod := (len(str_to_encode) % 3):
            groups.append(self.int_to_bin(int(str_to_encode[-mod:]), mod * 3 + 1))
        groups = ''.join(groups)
        return groups


    def __encode_letter_digit(self, str_to_encode: str) -> str:
        """
        Кодирует строку
        :param str_to_encode: Строка для кодирования
        :return: Побитово закодированная строка
        """
        groups = [TABLE_1.find(l) for l in str_to_encode]
        groups = [groups[i * 2] * 45 + groups[i * 2 + 1] for i in range(len(groups) // 2)]
        groups = list(map(lambda x: Generator.int_to_bin(x, 11), groups))
        if len(str_to_encode) % 2:
            groups.append(self.int_to_bin(TABLE_1.find(str_to_encode[-1]), 6))
        return ''.join(groups)


    def __encode_bytecode(self, str_to_encode: str) -> str:
        """
        Кодирует строку побайтово
        :param str_to_encode: Строка
        :return: Закодированная побитово строка
        """
        byte = self.int_to_bin(int(str_to_encode.encode(self.encoding).hex(), 16))
        return byte


    def __add_meta(self, encoded_str: str, encoding_method: EncodingMethod, symbols_count: int) -> tuple[int, str]:
        """
        Добавление мета информации и поиск версии
        :param encoded_str: побитовая строка
        :param encoding_method: метод кодирования
        :param symbols_count: количество символов
        :return: версия и строка с мета информацией
        """
        encoded_length = len(encoded_str) // 8 if encoding_method == EncodingMethod.BYTECODE else symbols_count
        for v in range(40):
            if v <= 9:
                meta_size = TABLE_3[encoding_method][0]
            elif v <= 26:
                meta_size = TABLE_3[encoding_method][1]
            else:
                meta_size = TABLE_3[encoding_method][2]
            if meta_size + len(encoded_str) <= TABLE_2[self.CL][v]:
                encoded_str = encoding_method.value + self.int_to_bin(encoded_length, meta_size) + encoded_str
                encoded_str = '0' * (8 - (len(encoded_str) % 8)) + encoded_str
                return v, encoded_str


    def encode(self, str_to_encode: str) -> None:
        if self.__define_method(str_to_encode) == EncodingMethod.ONLY_DIGIT:
            binary = self.__encode_only_digit(str_to_encode)
            encoding_method = EncodingMethod.ONLY_DIGIT
        elif self.__define_method(str_to_encode) == EncodingMethod.LETTER_DIGIT:
            binary = self.__encode_letter_digit(str_to_encode)
            encoding_method = EncodingMethod.LETTER_DIGIT
        elif self.__define_method(str_to_encode) == EncodingMethod.BYTECODE:
            binary = self.__encode_bytecode(str_to_encode)
            encoding_method = EncodingMethod.BYTECODE
        else:
            raise UndefinedMethodException('Метод кодирования не определен')

        version, binary = self.__add_meta(binary, encoding_method, len(str_to_encode))
        blocks = self.__division_to_blocks(binary, version)
        print(*map(len, blocks), sep='\n')


    def __division_to_blocks(self, encoded_str: str, version: int) -> list[str]:
        """
        Делит на блоки
        :param encoded_str: закодированная строка
        :param version: версия
        :return: Блоки и количество байт в них
        """
        block_count = TABLE_4[self.CL][version]
        bytes_count = len(encoded_str) // 8
        block_size, extra_bytes = divmod(bytes_count, block_count)
        str_1, str_2 = encoded_str[:(block_count - extra_bytes) * block_size * 8], \
                       encoded_str[(block_count - extra_bytes) * block_size * 8:]
        blocks = [str_1[i * block_size: (i + 1) * block_size] for i in range(block_count - extra_bytes)]
        blocks += [str_2[i * (block_size + 1): (i + 1) * (block_size + 1)] for i in range(extra_bytes)]
        assert sum(map(len, blocks)) == len(encoded_str) // 8
        return blocks


    def __correction_bytes_creation(self, version: int, blocks: list[str]):
        """
        Определяет сколько байтов коркоррекции надо создать, по количеству байтов определяет генерирующий многочлен
        :param version: Версия кодирования
        :param blocks: Список строк, представляющих собой блоки
        :return: Готовая для печати на картинке строка битов
        """
        corr_bytes_count = TABLE_5[self.CL][version]
        polynom = TABLE_6[corr_bytes_count]
        corr_bytes = []
        for block in blocks:
            array = [int(block[i * 8: (i + 1) * 8], 2) for i in range(len(block) // 8)]

            if corr_bytes_count > len(array):
                array += [0] * (corr_bytes_count - len(array))

            for _ in range(len(array)):
                a = array.pop(0)
                array.append(0)
                if a:
                    b = TABLE_8[a]
                    for i in range(corr_bytes_count):
                        b += polynom[i]
                        b %= 255
                        # побитовое сложеие
                        c = TABLE_7[b]
                        array[i] = c ^ array[i]
            corr_bytes.append(array[:corr_bytes_count])

        result = []
        for i in range(max(map(len, blocks))):
            for block in blocks:

                # Здесь заканчиватся код Софушки
                if i < len(block):
                    result.append(block[i])

        for i in range(max(map(len, corr_bytes))):
            for corr in corr_bytes:
                result.append(corr[i])

        return ''.join(result)

