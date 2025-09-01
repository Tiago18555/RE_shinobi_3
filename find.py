import binascii

def find_hex_in_file(file_path, hex_value):
    offsets = []
    hex_value = binascii.unhexlify(hex_value)

    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            offset = content.find(hex_value)
            while offset != -1:
                offsets.append(offset)
                offset = content.find(hex_value, offset + 1)
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    return offsets

file_path = input("Digite o caminho do arquivo .bin (ou 'sair' para encerrar): ")

while True:

    hex_value = input("Digite o valor em hexadecimal a ser procurado: ")
    if not hex_value:
        print("Valor hexadecimal não pode ser vazio.")
        continue

    offsets = find_hex_in_file(file_path, hex_value)
    
    if offsets:
        print("Offsets em hexadecimal:", [hex(offset) for offset in offsets])
    else:
        print(f"Valor {hex_value} não encontrado no arquivo {file_path}.")