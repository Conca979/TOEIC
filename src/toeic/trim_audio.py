from __future__ import annotations

import hashlib
from pathlib import Path

FRAMES_TO_TRIM = 689  # 689 frames * 1152 / 44100 Hz = 17.998s (Korean intro + jingle)
INTRO_PREFIX_HASHES = {
    "c6b10eee3a950af7",
    "41ac98ed51cc7485",
    "edb9aedd891633a0",
}


def parse_id3v2_end(data: bytes) -> int:
    """Return byte offset immediately after the ID3v2 header, or 0 if absent."""
    if len(data) >= 10 and data[:3] == b"ID3":
        size = (
            ((data[6] & 0x7F) << 21)
            | ((data[7] & 0x7F) << 14)
            | ((data[8] & 0x7F) << 7)
            | (data[9] & 0x7F)
        )
        return 10 + size
    return 0


def find_frame_cut_offset(data: bytes, start_offset: int, frame_count: int) -> int:
    """Walk `frame_count` MPEG-1 Layer III 128kbps 44.1kHz frames and return the cut offset."""
    pos = data.find(b"\xff\xfb", start_offset)
    if pos < 0:
        raise RuntimeError(f"No MP3 sync header found at or after offset {start_offset}")
    for idx in range(frame_count):
        if pos + 4 > len(data) or data[pos] != 0xFF or (data[pos + 1] & 0xE0) != 0xE0:
            raise RuntimeError(f"Invalid MP3 frame sync at frame {idx} (offset {pos})")
        padding = (data[pos + 2] >> 1) & 1
        pos += 417 + padding
    if pos + 4 > len(data) or data[pos] != 0xFF or (data[pos + 1] & 0xE0) != 0xE0:
        raise RuntimeError(f"Invalid MP3 frame sync at cut offset {pos}")
    return pos


def trim_mp3_intro(mp3_path: Path) -> tuple[bool, int]:
    """Losslessly strip the 18.0s Korean intro from a Hackers TOEIC MP3 file."""
    data = mp3_path.read_bytes()
    id3_end = parse_id3v2_end(data)
    prefix_hash = hashlib.sha256(data[id3_end : id3_end + 16000]).hexdigest()[:16]

    if prefix_hash not in INTRO_PREFIX_HASHES:
        return False, len(data)

    cut_pos = find_frame_cut_offset(data, id3_end, FRAMES_TO_TRIM)
    trimmed = data[:id3_end] + data[cut_pos:]
    mp3_path.write_bytes(trimmed)
    return True, len(trimmed)


def trim_all_audio(audio_dir: Path = Path("Hacker 3/AUDIO")) -> None:
    for test_id in range(1, 11):
        mp3_path = audio_dir / f"TEST {test_id}.mp3"
        changed, new_size = trim_mp3_intro(mp3_path)
        status = "TRIMMED" if changed else "ALREADY TRIMMED (skipped)"
        print(f"TEST {test_id:02d}: {status} ({new_size:,} bytes)")


def main() -> None:
    trim_all_audio()


if __name__ == "__main__":
    main()
