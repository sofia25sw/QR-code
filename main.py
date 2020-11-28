from classes.QRGenerator import Generator

if __name__ == '__main__':
    g = Generator(correction_level='M', encoding='utf-8')
    g.encode('а'*90)
    # print('010001100100')