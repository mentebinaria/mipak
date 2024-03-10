'''
Math Invaders - Windows 95 game - PAK parser and creation tool

Copyright (C) 2024 Mente Binária

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import argparse
import os
import struct
from pathlib import Path

'''
Math Invaders PAK file definition:

struct entry {
    char path[64];
    le u32 offset;
};

struct mi_pak {
    le u32 num_entries;
    entry entries[num_entries];
    entry mysterious;
};
'''

class MathInvadersPakFile:
    '''Pack upack PAK files used by Math Invaders game'''
    def __init__(self, pak_filename=None):
        if not pak_filename:
            self.num_entries = 0
            self.entries = []
            return

        self.pak_filename = pak_filename
        with open(self.pak_filename, 'rb') as f:
            self.num_entries = struct.unpack('<I', f.read(4))[0]
            self.entries = []

            for _ in range(self.num_entries):
                entry_path = f.read(64).decode('ascii')
                entry_path = entry_path.rstrip('\x00').replace('\\', os.sep)
                offset = struct.unpack('<I', f.read(4))[0]
                self.entries.append([entry_path, offset])


    def print_entries(self):
        for file_path, offset in self.entries:
            print(file_path, hex(offset))


    def unpack(self, output_dir):
        for i, (entry_path, offset) in enumerate(self.entries):
            file_path = os.path.join(output_dir, entry_path)
            print(f'Unpacking {file_path}')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if i < (self.num_entries - 1):
                next_offset = self.entries[i + 1][1]
                size = next_offset - offset
            else:
                # Último elemento da lista
                size = None
            
            with open(self.pak_filename, 'rb') as f:
                f.seek(offset)
                with open(file_path, 'wb') as g:
                    g.write(f.read(size))

        print(f'{self.num_entries} files unpacked from {self.pak_filename}')
                    

    def pack(self, input_dir, pak_filename):
        self.pak_filename = pak_filename
        p = Path(pak_filename)
        if p.exists():
            os.unlink(pak_filename)

        # Percorre uma vez pra pegar quantos arquivos tem lá
        for _, _, files in os.walk(input_dir):
            # Adiciona a quantidade de arquivos no diretório atual
            self.num_entries += len(files)

        # O offset do primeiro arquivo vem depois do cabeçalho, que
        # tem 4 bytes (número de entradas), mais 68 bytes * número de entradas
        # e mais uma entrada misteriosa de 68 bytes
        offset = 4 + ((self.num_entries + 1) * 68)
        file_size = 0
        for root, _, files in os.walk(input_dir):            
            for file in files:
                file_path = os.path.join(root, file)
                # Remove o input_dir para criar o entry_path, que vai
                # para o cabeçalho
                entry_path = file_path[len(input_dir) + 1:]
                offset += file_size
                self.entries.append([entry_path, offset])
                file_size = os.path.getsize(file_path)
                print(f'Packing {file_path}')

                with open(file_path, 'rb') as f:
                    with open(pak_filename, 'ab') as g:
                        g.write(f.read())

        # Agora tem que abrir o arquivo PAK de novo, dessa vez
        # para pra inserir o cabeçalho e a entrada misteriosa
        with open(pak_filename, "r+b") as f:
            existing_data = f.read()
            f.seek(0)

            # Começo a escrever o cabeçalho
            f.write(self.num_entries.to_bytes(4, byteorder='little'))
            
            for entry_path, offset in self.entries:
                fmt_path = entry_path.ljust(64, '\x00')
                fmt_path = fmt_path.replace('/', '\\')
                f.write(fmt_path.encode(encoding='ascii'))
                f.write(offset.to_bytes(4, byteorder='little'))
            
            mysterious = bytes([
                0x00, 0x00, 0x00, 0x00, 0xBC, 0x42, 0x59, 0x81, 0x00, 0x00, 0x00, 0x00, 0x8C, 0x83, 0x59, 0x81, 
                0x8C, 0x83, 0x59, 0x81, 0x88, 0x83, 0x59, 0x81, 0x3B, 0xAE, 0xF7, 0xBF, 0x00, 0x20, 0x56, 0x81, 
                0x00, 0x00, 0x00, 0x00, 0x8C, 0x83, 0x59, 0x81, 0xDB, 0xAE, 0xF7, 0xBF, 0x8C, 0x83, 0x59, 0x81, 
                0xDE, 0xDA, 0xF7, 0xBF, 0x8C, 0x83, 0x59, 0x81, 0x8C, 0x83, 0x59, 0x81, 0xE2, 0x13, 0xF7, 0xBF, 
                0x59, 0xB7, 0x5E, 0x01, 
            ])
            f.write(mysterious)
            f.write(existing_data)

        print(f'{self.num_entries} files packed to {self.pak_filename}')


def parse_arguments():
    parser = argparse.ArgumentParser(
            description='Pack/unpack Math Invaders PAK files')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('--dir', '-d', metavar='DIRECTORY', default='pak_files',
                        help='working directory (default: pak_files)')
    group.add_argument('--pack', '-p', action='store_true',
                       help='pack/create a new PAK file')
    group.add_argument('--unpack', '-u', action='store_true',
                       help='unpack a PAK file')
    parser.add_argument('file', nargs=1,
                        help='PAK file name')
    parsed = parser.parse_args()
    return parsed


if __name__ == "__main__":
    args = parse_arguments()

    if args.unpack:
        mip = MathInvadersPakFile(args.file[0])
        mip.unpack(args.dir)
    elif args.pack:
        mip = MathInvadersPakFile()
        mip.pack(args.dir, args.file[0])
