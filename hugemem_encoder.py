import base64
import zlib

def huge_string_to_list(encoded_str):

    compressed_data = base64.b64decode(encoded_str)

    decompressed_data = zlib.decompress(compressed_data, wbits=-15)

    liste = []
    for i in range(0, len(decompressed_data), 2):
        if i + 1 < len(decompressed_data):
            value = decompressed_data[i] | (decompressed_data[i + 1] << 8)
            liste.append(value)
    return liste

def list_to_huge_string(data):
    if len(data) != 1<<16:
        raise ValueError(f'expected table size of 65536 '
                         f'but got {len(data)}')
    lower_16 = bytearray()
    upper_16 = bytearray()

    for value in data:
        if value > 0xFFFFFFFF:
            print(f'\033[0;31mWarning: {value} > 32 bit\033[0m')
        lower = value & 0xFFFF
        upper = (value >> 16) & 0xFFFF

        lower_16.append(lower & 0xFF)
        lower_16.append((lower >> 8) & 0xFF)

        upper_16.append(upper & 0xFF)
        upper_16.append((upper >> 8) & 0xFF)

    compressed_lower = zlib.compress(lower_16, level=2, wbits=-15)
    compressed_upper = zlib.compress(upper_16, level=2, wbits=-15)

    encoded_lower = base64.b64encode(compressed_lower).decode('utf-8').strip('=')
    encoded_upper = base64.b64encode(compressed_upper).decode('utf-8').strip('=')

    return encoded_upper, encoded_lower
