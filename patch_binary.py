"""Add one compatibility library to an exact, already-thinned GSE executable."""
import hashlib
import struct
from pathlib import Path

BUILDS = {
    "arm64": (0x100000C, "dbb4738181c9fb9261a36a86df4377265a5e92170aa7175b698a1d04a0a08412"),
    "x86_64": (0x1000007, "c1daf45f3c33e4ae3082aaef080b1979469dfa9a168f616bf74d8e5d7ceeccff"),
}

# Existing NSApplicationMain import stubs, verified in each supported binary.
# Direct distribution uses standard AppKit startup instead of the legacy
# Mac App Store receipt wrapper. No receipt or Apple identity is synthesized.
DESKTOP_ENTRIES = {
    "arm64": (0x1CCFBC, 0x1413C14, bytes.fromhex("904a00b010c645f900021fd6")),
    "x86_64": (0x1DB5EC, 0x184AF46, bytes.fromhex("ff2584ec8200")),
}


def select_desktop_entry(data, original_entry, appkit_entry, expected_stub):
    b = bytearray(data)
    if len(b) < 32 or appkit_entry < 32 or b[appkit_entry:appkit_entry + len(expected_stub)] != expected_stub:
        raise ValueError("Unexpected AppKit entry stub")
    count, size = struct.unpack_from("<II", b, 16)
    end, pos = 32 + size, 32
    if end > len(b):
        raise ValueError("Invalid load-command table")
    entries = []
    for _ in range(count):
        if pos + 8 > end:
            raise ValueError("Truncated load command")
        cmd, cmdsize = struct.unpack_from("<II", b, pos)
        if cmdsize < 8 or pos + cmdsize > end:
            raise ValueError("Invalid load command")
        if cmd == 0x80000028:
            if cmdsize != 24 or struct.unpack_from("<Q", b, pos + 8)[0] != original_entry:
                raise ValueError("Unexpected original application entry")
            entries.append(pos + 8)
        pos += cmdsize
    if pos != end or len(entries) != 1:
        raise ValueError("Expected exactly one LC_MAIN")
    struct.pack_into("<Q", b, entries[0], appkit_entry)
    return bytes(b)


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
    desktop = select_desktop_entry(original, *DESKTOP_ENTRIES[arch])
    path.write_bytes(add_load_command(desktop, cpu))
