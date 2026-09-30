# GSE SMART IPTV macOS compatibility release

Compatibility fixes for **GSE SMART IPTV 4.4 (52)**: playlist double-click navigation on macOS 27 and the reported empty EPG update-queue crash.

## Downloads

Download the complete app for your Mac from [Releases](https://github.com/Delitants/gse-smart-iptv-macos-compat/releases).

| Download | Architecture | Validation |
| --- | --- | --- |
| `GSE-SMART-IPTV-4.4-compat-1.0.0-arm64.zip` | Apple Silicon only | Native tests and live macOS 27 playlist/EPG checks |
| `GSE-SMART-IPTV-4.4-compat-1.0.0-x86_64.zip` | Intel only | x86_64 tests under Rosetta; physical Intel Mac testing pending |

**Requires your own existing GSE App Store installation and receipt.** No receipt is distributed. GSE 4.4 uses the obsolete `exit(173)` receipt-refresh flow, which fails on macOS 27; preserve your own receipt before replacing the app. The commands below keep it locally and never upload it:

```sh
# After unzipping the correct architecture into Downloads, with GSE quit:
cp -R "/Applications/GSE SMART IPTV.app/Contents/_MASReceipt" \
  "$HOME/Downloads/GSE SMART IPTV.app/Contents/_MASReceipt"
```

Then back up your old app and move the downloaded app to Applications. Do not distribute or share your receipt. A fresh installation without an existing valid receipt has not been validated.

Both downloads contain an app named `GSE SMART IPTV.app`. Quit GSE, retain a backup of your current app, unzip the appropriate download, and copy the app to Applications. Keep only one copy running. The bundle identifier is unchanged so the app can reuse an existing GSE profile. macOS may ask permission to access its existing app data after the local signature changes.

These builds are locally signed, not Developer ID notarized. If macOS requires approval, use its normal per-app approval controls. No system-wide security change is required. No playlists, accounts, preferences or EPG databases are bundled in either download. App Store receipts, extended attributes, vendor sample playlists are removed. The required vendor logo mapping contains only PNG image links and is retained. Existing local user data is preserved; sample-import actions have no bundled samples to load.

The app retains its sandbox and the original selected-file, Movies and network permissions. The compatibility code neither reads nor uploads account data. The original application's network behavior and bundled services are otherwise unchanged.

## Changes

- Assign the existing table delegate as the target for `doubleClickedRow:` when the target is missing and the delegate implements the action. Explicit targets and other actions are unchanged.
- At the one identified EPG completion call site, ignore removal of index zero when its queue is already empty. Other array errors still raise their normal exceptions.
- The shim activates only for the documented binary UUID of each supported architecture. It adds one library load command; it does not rewrite the original application's machine instructions or licensing logic.

The EPG change contains the reported crash. It does not replace the application's asynchronous update design or guarantee that every unrelated crash is fixed.

## Validation

- 9 native behavior tests per architecture, including actual Objective-C message dispatch at a controlled native return address.
- 6 Mach-O patcher tests: both architectures, preservation of section contents, architecture mismatch, header bounds, and unused-header-space checks.
- Apple Silicon live checks: existing profile, playlist download, channel-group navigation, EPG import and populated program timeline.
- Intel behavior tests run through Rosetta on Apple Silicon. A physical Intel Mac and a prolonged playback/stability run have not been tested.

## Build from an authorized local copy

Requires macOS, Python 3, and Xcode Command Line Tools. The builder accepts only the documented original executable fingerprints and refuses to overwrite an existing destination.

```sh
python3 build.py --source '/Applications/GSE SMART IPTV.app' \
  --output './build/arm64/GSE SMART IPTV.app' --arch arm64
python3 build.py --source '/Applications/GSE SMART IPTV.app' \
  --output './build/x86_64/GSE SMART IPTV.app' --arch x86_64
python3 -m unittest discover -s tests -p 'test_*.py' -v
./test.sh arm64
./test.sh x86_64
```

The Intel test requires Rosetta when run on Apple Silicon. Compilation targets macOS 11+ for ARM and 10.13+ for Intel; older systems have not been validated.

| Architecture | Original UUID | EPG return offset |
| --- | --- | --- |
| arm64 | `79A5CB6C-8184-3ADA-9683-B35FB3DA390E` | `0x1bada0` |
| x86_64 | `DF386371-A77F-3D79-9166-4E4B9DC47A2A` | `0x1c8cdd` |

To roll back, quit this build and restore your backed-up app. No profile reset is required.

## Licensing

The compatibility source, build scripts and tests in this repository are MIT licensed. That license does not cover the bundled original GSE application, artwork or third-party components; their original rights and notices remain. GSE SMART IPTV is a product of GSE TECHNOLOGY LTD. This is an independent compatibility release, not an official vendor update.
