#!/usr/bin/env python3
"""Build sanitized, architecture-specific app bundles from an authorized local source."""
import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path
from patch_binary import patch

ROOT = Path(__file__).resolve().parent
VERSION = "1.1.0"


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def build(source, output, arch):
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Output already exists; choose a new path")
    info = plistlib.loads((source / "Contents/Info.plist").read_bytes())
    if (info.get("CFBundleIdentifier"), info.get("CFBundleShortVersionString"), info.get("CFBundleVersion")) != ("com.gsetech.gseosxiptvpro", "4.4", "52"):
        raise ValueError("Expected GSE SMART IPTV 4.4 (52)")
    # Copy only the application, never its container, preferences, keychain or logs.
    run("ditto", "--noextattr", "--norsrc", "--noqtn", "--noacl", source, output)
    for private in ("_MASReceipt", "_CodeSignature", "embedded.provisionprofile"):
        p = output / "Contents" / private
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    for p in output.rglob(".DS_Store"):
        p.unlink()
    # Public bundles contain no playlists, including the vendor's samples. Existing user data is outside this bundle.
    resources = output / "Contents/Resources"
    for p in resources.rglob("*"):
        if p.is_file() and (p.suffix.lower() in {".m3u", ".m3u8", ".pls", ".xspf"}
                            or p.name == "gsefile_jsonsample.json"):
            p.unlink()
    executable = output / "Contents/MacOS" / info["CFBundleExecutable"]
    thin = executable.with_name("GSE-thin.tmp")
    run("lipo", executable, "-thin", arch, "-output", thin)
    thin.replace(executable)
    patch(executable, arch)
    executable.chmod(0o755)
    frameworks = output / "Contents/Frameworks"
    frameworks.mkdir(exist_ok=True)
    library = frameworks / "GSECompatibility.dylib"
    minimum = "11.0" if arch == "arm64" else "10.13"
    run("xcrun", "clang", "-arch", arch, "-mmacosx-version-min=" + minimum,
        "-fobjc-arc", "-O2", "-dynamiclib", "-framework", "Cocoa",
        "-install_name", "@executable_path/../Frameworks/GSECompatibility.dylib",
        ROOT / "src/GSECompatibility.m", "-o", library)
    info["GSECompatibilityVersion"] = VERSION
    info["LSArchitecturePriority"] = [arch]
    info["LSMinimumSystemVersion"] = minimum
    (output / "Contents/Info.plist").write_bytes(plistlib.dumps(info))
    run("xattr", "-cr", output)
    run("codesign", "--force", "--sign", "-", library)
    run("codesign", "--force", "--sign", "-", "--entitlements", ROOT / "compat-entitlements.plist", output)
    run("codesign", "--verify", "--deep", "--strict", output)
    print("Built", arch, output.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arch", choices=("arm64", "x86_64"), required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.arch)
