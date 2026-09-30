import struct
import unittest
from patch_binary import add_load_command


def fixture(cpu=0x100000C, section=512):
    b = bytearray(1024)
    struct.pack_into("<IIIIIIII", b, 0, 0xFEEDFACF, cpu, 0, 2, 1, 152, 0, 0)
    struct.pack_into("<II", b, 32, 0x19, 152)
    struct.pack_into("<I", b, 96, 1)
    struct.pack_into("<I", b, 152, section)
    b[512:] = b"X" * 512
    return bytes(b)


class HeaderTests(unittest.TestCase):
    def test_both_architectures_preserve_section_contents(self):
        for cpu in (0x100000C, 0x1000007):
            original = fixture(cpu)
            result = add_load_command(original, cpu)
            self.assertEqual(result[512:], original[512:])
            self.assertEqual(len(result), len(original))
            self.assertEqual(struct.unpack_from("<I", result, 16)[0], 2)
            self.assertEqual(struct.unpack_from("<I", result, 184)[0], 0xC)
            self.assertIn(b"@executable_path/../Frameworks/GSECompatibility.dylib\0", result[184:512])

    def test_wrong_architecture(self):
        with self.assertRaises(ValueError):
            add_load_command(fixture(), 0x1000007)

    def test_insufficient_padding(self):
        with self.assertRaises(ValueError):
            add_load_command(fixture(section=192), 0x100000C)

    def test_nonzero_padding(self):
        b = bytearray(fixture())
        b[185] = 1
        with self.assertRaises(ValueError):
            add_load_command(bytes(b), 0x100000C)

    def test_truncated_header(self):
        with self.assertRaises(ValueError):
            add_load_command(b"", 0x100000C)

    def test_bad_command_size(self):
        b = bytearray(fixture())
        struct.pack_into("<I", b, 36, 4)
        with self.assertRaises(ValueError):
            add_load_command(bytes(b), 0x100000C)


if __name__ == "__main__":
    unittest.main()
