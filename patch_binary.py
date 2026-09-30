"""Add one compatibility library to an exact, already-thinned GSE executable."""
import hashlib
import struct
from pathlib import Path

BUILDS = {
    "arm64": (0x100000C, "dbb4738181c9fb9261a36a86df4377265a5e92170aa7175b698a1d04a0a08412"),
    "x86_64": (0x1000007, "c1daf45f3c33e4ae3082aaef080b1979469dfa9a168f616bf74d8e5d7ceeccff"),
}


def add_load_command(data: bytes, cpu: int) -> bytes:
    b = bytearray(data)
    if len(b) < 32 or struct.unpack_from("<II", b) != (0xFEEDFACF, cpu):
        raise ValueError("Expected a thin 64-bit Mach-O for the selected architecture")
    count, size = struct.unpack_from("<II", b, 16)
    end = 32 + size
    if end > len(b):
        raise ValueError("Invalid load-command table")
    pos = 32
    first_section = len(b)
    for _ in range(count):
        if pos + 8 > end:
            raise ValueError("Truncated load command")
        cmd, cmdsize = struct.unpack_from("<II", b, pos)
        if cmdsize < 8 or pos + cmdsize > end:
            raise ValueError("Invalid load-command size")
        if cmd == 0x19:
            if cmdsize < 72:
                raise ValueError("Truncated segment")
            nsects = struct.unpack_from("<I", b, pos + 64)[0]
            if 72 + nsects * 80 > cmdsize:
                raise ValueError("Truncated sections")
            for index in range(nsects):
                offset = struct.unpack_from("<I", b, pos + 72 + index * 80 + 48)[0]
                if offset:
                    first_section = min(first_section, offset)
        pos += cmdsize
    if pos != end:
        raise ValueError("Inconsistent load-command table")
    name = b"@executable_path/../Frameworks/GSECompatibility.dylib\0"
    command_size = (24 + len(name) + 7) & ~7
    if end + command_size > first_section or any(b[end:end + command_size]):
        raise ValueError("Insufficient unused header space")
    command = struct.pack("<IIIIII", 0xC, command_size, 24, 0, 0x10000, 0x10000)
    b[end:end + command_size] = (command + name).ljust(command_size, b"\0")
    struct.pack_into("<II", b, 16, count + 1, size + command_size)
    return bytes(b)


def patch(path: Path, arch: str) -> None:
    cpu, digest = BUILDS[arch]
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != digest:
        raise ValueError("Unsupported GSE executable. Only the documented 4.4 (52) build is supported.")
    path.write_bytes(add_load_command(original, cpu))
