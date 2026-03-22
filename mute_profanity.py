#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python script to mute profanity in a video file using AI-based transcription.

import subprocess
import time
import sys
import os
import torch
import argparse
import json
from faster_whisper import WhisperModel
import gc

os.environ["FFMPEG_BINARY"] = "ffmpeg"
os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"


def log(message: str, flush: bool = True) -> None:
    print(message, flush=flush)


def safe_remove(path):
    for _ in range(3):
        try:
            os.remove(path)
            return
        except PermissionError:
            time.sleep(5)


# ====================== BUILT-IN PROFANITY + VARIANTS ======================

BUILTIN_PROFANE_WORDS = {
    "fuck", "shit", "ass", "bitch", "bastard", "cunt", "dick", "piss", "cock", "tit",
    "fucker", "motherfucker", "asshole", "damn", "hell", "asshat", "bullshit", "crap",
    "god", "jesus christ", "son of a bitch"
}

VARIANTS = {
    "fuck": ["fck", "f*ck", "fk", "fuk", "phuck"],
    "shit": ["sh*t", "sht", "sh1t"],
    "ass": ["a$$", "a*s", "azz"],
    "bitch": ["b*tch", "btch", "bich"],
    "cunt": ["c*nt", "cnt"],
    "dick": ["d*ck", "dik"],
    "motherfucker": ["mf", "mfer", "motherf*cker"],
    "asshole": ["a$$hole", "assh0le"],
    "damn": ["d*mn", "dam"],
    "hell": ["h*ll"]
}


def expand_variants(words: set) -> set:
    """Expand common variants of profanity words."""
    expanded = set(words)
    for base, vars_list in VARIANTS.items():
        if base in expanded:
            expanded.update(vars_list)
    return expanded


# ====================== HELPERS ======================


def parse_srt_time(time_str):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def parse_srt(srt_path):
    if not os.path.exists(srt_path):
        return []
    subs = []
    try:
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f.readlines()]
        i = 0
        while i < len(lines):
            if lines[i].isdigit():
                i += 1
                if i < len(lines) and '-->' in lines[i]:
                    start_str, end_str = [x.strip() for x in lines[i].split('-->')]
                    start_ms = parse_srt_time(start_str)
                    end_ms = parse_srt_time(end_str)
                    i += 1
                    text_lines = []
                    while i < len(lines) and lines[i] and not lines[i].isdigit():
                        text_lines.append(lines[i])
                        i += 1
                    text = ' '.join(text_lines).strip()
                    if text:
                        subs.append((start_ms, end_ms, text))
                else:
                    i += 1
            else:
                i += 1
    except Exception:
        pass
    return subs


def merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [list(intervals[0])]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            last[1] = max(last[1], current[1])
        else:
            merged.append(list(current))
    return [tuple(x) for x in merged]


def get_best_english_subtitle_index(input_file):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 's', input_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])

        candidates = []
        for sub_idx, stream in enumerate(streams):
            tags = stream.get('tags', {})
            lang = tags.get('language', '').lower()
            if lang not in ('eng', 'en'):
                continue
            disposition = stream.get('disposition', {})
            is_forced = bool(disposition.get('forced', 0))
            title = tags.get('title', '').lower()

            score = 0
            if not is_forced: score += 100
            if 'sdh' not in title and 'hearing' not in title and 'captions' not in title: score += 30
            if 'english' in title or title == 'en': score += 20
            if disposition.get('default', 0): score += 10

            candidates.append((sub_idx, score, title, is_forced))

        if not candidates:
            return None

        best = max(candidates, key=lambda x: x[1])
        log(f"Selected subtitle stream: 0:s:{best[0]} (title: '{best[2]}', forced: {best[3]})")
        return best[0]

    except Exception as e:
        log(f"ffprobe subtitle detection failed: {e} (falling back)")
        return None


def get_best_english_audio_index(input_file):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a', input_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])

        candidates = []
        for a_idx, stream in enumerate(streams):
            tags = stream.get('tags', {})
            lang = tags.get('language', '').lower()
            if lang not in ('eng', 'en'): continue

            disposition = stream.get('disposition', {})
            title = tags.get('title', '').lower()
            codec = stream.get('codec_name', '').lower()
            bitrate = int(stream.get('bit_rate', 0) or 0)

            score = 150
            if 'original' in title or 'eng' in title or 'english' in title: score += 80
            if 'atmos' in title or 'atmos' in codec or bitrate > 700000: score += 60
            if 'eac3' in codec or 'ac3' in codec: score += 20
            if disposition.get('default', 0): score += 30
            if disposition.get('forced', 0): score -= 50

            candidates.append((a_idx, score, title, bitrate, codec))

        if not candidates:
            log("No English audio track found → using first audio stream (0:a:0)")
            return 0

        best = max(candidates, key=lambda x: x[1])
        log(f"Selected English audio stream: 0:a:{best[0]} (title: '{best[2]}', bitrate: {best[3]//1000}kb/s, codec: {best[4]})")
        return best[0]

    except Exception as e:
        log(f"ffprobe audio detection failed: {e} → falling back to first audio stream")
        return 0


def get_audio_stream_count(input_file):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a', input_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return len(data.get('streams', []))
    except Exception:
        log("ffprobe audio count failed → assuming 1 track")
        return 1


def run_subprocess(cmd, quiet=False):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not quiet and result.stdout:
        for line in result.stdout.strip().splitlines():
            log(line)
    if result.returncode != 0:
        raise ValueError(f"Subprocess failed with code {result.returncode}")


def load_profanity_words(custom_path=None, merge=True):
    """Load profanity words. If merge=True, combine custom + built-in + variants."""
    words = set()

    if custom_path and os.path.isfile(custom_path):
        try:
            with open(custom_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    cleaned = line.lower()
                    if cleaned:
                        words.add(cleaned)
            log(f"Loaded {len(words)} entries from custom list: {custom_path}")
        except Exception as e:
            log(f"Error reading custom list: {e}")

    if merge or not words:
        words.update(BUILTIN_PROFANE_WORDS)
        words = expand_variants(words)
        if merge and custom_path:
            log(f"Merged with built-in list. Total unique terms: {len(words)}")
        else:
            log(f"Using built-in list + variants. Total: {len(words)}")

    return words


def mute_profanity(input_file, output_file, model=None, validate=False, safe=False, whisper_model="large-v3", 
                   beam_size=5, enhance=False, quiet=False, custom_words=None, merge=True):
    
    if os.path.exists(output_file):
        log(f"Output file '{output_file}' already exists. Removing it to proceed.")
        os.remove(output_file)

    pid = os.getpid()
    audio_path = f"temp_audio_{pid}.flac"
    temp_srt_path = f"temp_subs_{pid}.srt"
    if not quiet:
        log(f"Using temporary files (PID {pid}): audio={audio_path}, subs={temp_srt_path}")

    try:
        best_audio_idx = get_best_english_audio_index(input_file)

        # ====================== DIALOGUE ENHANCEMENT ======================
        if enhance:
            log("Applying Dialogue Enhancement (high-pass + low-pass + normalization)...")
            enhanced_audio = f"temp_enhanced_{pid}.flac"
            enhance_cmd = [
                'ffmpeg', '-y', '-i', input_file,
                '-map', f'0:a:{best_audio_idx}',
                '-af', 'highpass=200,lowpass=3500,dynaudnorm',
                '-vn', '-acodec', 'flac',
                enhanced_audio
            ]
            run_subprocess(enhance_cmd, quiet=quiet)
            audio_to_use = enhanced_audio
        else:
            audio_to_use = audio_path
            log("Starting audio extraction...")
            extract_cmd = [
                'ffmpeg', '-y', '-i', input_file,
                '-map', f'0:a:{best_audio_idx}',
                '-vn', '-acodec', 'flac',
                audio_path
            ]
            run_subprocess(extract_cmd, quiet=quiet)

        if model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            log(f"Using device: {device} with compute_type: {compute_type} and model: {whisper_model}")
            model = WhisperModel(whisper_model, device=device, compute_type=compute_type)
        else:
            log("Reusing pre-loaded Whisper model (batch mode)")

        if safe:
            log("SAFE MODE ENABLED...")

        log(f"Starting transcription with beam_size={beam_size}...")
        segments, info = model.transcribe(audio_to_use, beam_size=beam_size, word_timestamps=True)
        log(f"Detected language: {info.language} with probability {info.language_probability}")

        # Load profanity words (with merge/variant support)
        profane_words = load_profanity_words(custom_words, merge=merge)

        mute_intervals = []
        for segment in segments:
            for word in segment.words:
                cleaned_word = word.word.lower().strip().replace('.', '').replace(',', '')
                if cleaned_word in profane_words:
                    start_ms = int(word.start * 1000)
                    end_ms = int(word.end * 1000)
                    mute_intervals.append((start_ms, end_ms))
                    if not quiet:
                        log(f"Muting profane word '{word.word}' from {start_ms}ms to {end_ms}ms")

        # ====================== VALIDATION + SAFE MODE ======================
        if validate or safe:
            log("Extracting English subtitles for validation/safe mode...")
            sub_idx = get_best_english_subtitle_index(input_file)

            if sub_idx is not None:
                extract_cmd = ['ffmpeg', '-y', '-i', input_file, '-map', f'0:s:{sub_idx}', '-c:s', 'srt', temp_srt_path]
            else:
                extract_cmd = ['ffmpeg', '-y', '-i', input_file, '-map', '0:s:m:language:eng', '-c:s', 'srt', temp_srt_path]

            run_subprocess(extract_cmd, quiet=quiet)

            if not os.path.exists(temp_srt_path) or os.path.getsize(temp_srt_path) == 0:
                log("No usable English subtitles found. Skipping validation/safe checks.")
            else:
                subs_list = parse_srt(temp_srt_path)

                subs_profanities = []
                for start_ms, end_ms, text in subs_list:
                    for word in text.split():
                        cleaned = word.strip('.,!?;:"\'()[]').lower()
                        if cleaned in profane_words:
                            h = start_ms // 3600000
                            m = (start_ms % 3600000) // 60000
                            s = (start_ms % 60000) // 1000
                            ms_part = start_ms % 1000
                            ts_str = f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"
                            subs_profanities.append((ts_str, cleaned, start_ms, end_ms))

                subs_count = len(subs_profanities)
                whisper_count = len(mute_intervals)

                log(f"Validation: Whisper detected {whisper_count} profanities | Subtitles had {subs_count}")

                missed = []
                for ts_str, word, sub_start, sub_end in subs_profanities:
                    matched = any(not (w_end < sub_start or w_start > sub_end)
                                  for w_start, w_end in mute_intervals)
                    if not matched:
                        missed.append((ts_str, word))

                if missed:
                    log(f"Found {len(missed)} profanities in subtitles NOT detected by Whisper:")
                    for ts, w in missed:
                        log(f"   {ts} : '{w}'")
                else:
                    log("All profanities in subtitles were also detected by Whisper.")

                if len(missed) > 5:
                    log(f"WARNING: {len(missed)} extra profanities in subtitles were NOT caught by Whisper!")

                if safe:
                    safe_intervals = []
                    for start_ms, end_ms, text in subs_list:
                        has_profane = any(
                            word.strip('.,!?;:"\'()[]').lower() in profane_words
                            for word in text.split()
                        )
                        if has_profane:
                            overlaps = any(not (w_end < start_ms or w_start > end_ms)
                                           for w_start, w_end in mute_intervals)
                            if not overlaps:
                                safe_intervals.append((start_ms, end_ms))

                    if safe_intervals:
                        log(f"SAFE MODE: Adding {len(safe_intervals)} missed subtitle blocks "
                            f"(full sentence mute for Whisper-missed profanities only)")
                        mute_intervals.extend(safe_intervals)

        # ====================== END VALIDATION/SAFE ======================

        mute_intervals = merge_intervals(mute_intervals)
        log(f"Total mute intervals after merge: {len(mute_intervals)}")

        mute_intervals_sec = [(start / 1000.0, end / 1000.0) for start, end in mute_intervals if start + 0.001 < end]
        has_mute = bool(mute_intervals_sec)
        audio_count = get_audio_stream_count(input_file)

        final_cmd = ['ffmpeg', '-y', '-i', input_file]

        if has_mute:
            filter_parts = [f"volume=0:enable='between(t,{start:.3f},{end:.3f})'" for start, end in mute_intervals_sec]
            filter_complex = f"[0:a:{best_audio_idx}]{','.join(filter_parts)}[mutedeng]"
            final_cmd.extend(['-filter_complex', filter_complex])
            final_cmd.extend([
                '-map', '0', '-map', f'-0:a:{best_audio_idx}', '-map', '[mutedeng]',
                '-c:v', 'copy', '-c:s', 'copy', '-c:a', 'copy',
                f'-c:a:{audio_count-1}', 'eac3', f'-b:a:{audio_count-1}', '640k',
                f'-ar:{audio_count-1}', '48000', f'-metadata:s:a:{audio_count-1}', 'language=eng'
            ])
        else:
            final_cmd.extend(['-map', '0', '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'copy'])

        final_cmd.extend(['-map_metadata', '0', output_file])

        log("Running final pass...")
        run_subprocess(final_cmd, quiet=quiet)
        log(f"Initial output saved to {output_file}")

        if output_file.lower().endswith('.mkv'):
            log("Remuxing with MKVToolNix + timestamp clean...")
            temp_mkv = output_file + ".tmp.mkv"
            clean_mkv = output_file + ".clean.mkv"
            try:
                run_subprocess(['mkvmerge', '-o', temp_mkv, output_file], quiet=quiet)
                clean_cmd = [
                    'ffmpeg', '-y', '-loglevel', 'error', '-hide_banner', '-i', temp_mkv,
                    '-map', '0', '-c', 'copy', '-fflags', '+genpts', '-avoid_negative_ts', 'make_zero', clean_mkv
                ]
                run_subprocess(clean_cmd, quiet=quiet)

                safe_remove(output_file)
                safe_remove(temp_mkv)
                os.rename(clean_mkv, output_file)
                log("Timestamp clean complete — VLC should now play smoothly.")
            except Exception as e:
                log(f"Remux/clean error: {e}. Keeping original output.")

    except Exception as e:
        log(f"Error: {e}")
    finally:
        for temp in [audio_path, temp_srt_path]:
            if os.path.exists(temp):
                safe_remove(temp)
        if 'enhanced_audio' in locals() and os.path.exists(enhanced_audio):
            safe_remove(enhanced_audio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mute profanity in videos using AI transcription + VLC HEVC freeze fix.")
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--batch', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--safe', action='store_true')
    parser.add_argument('--model', default='large-v3', choices=['tiny','base','small','medium','large-v2','large-v3','distil-large-v3','large-v3-turbo'])
    parser.add_argument('--beam', type=int, default=5)
    parser.add_argument('--enhance', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--custom-words', type=str, default=None)
    parser.add_argument('--no-merge', action='store_true', help='Do not merge custom list with built-in list')

    args = parser.parse_args()

    if args.batch:
        if not os.path.isdir(args.input):
            log("ERROR: In --batch mode, the input must be a directory.")
            sys.exit(1)
        if os.path.isfile(args.output):
            log("ERROR: In --batch mode, the output must be a directory (not a file).")
            sys.exit(1)

        os.makedirs(args.output, exist_ok=True)
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.webm', '.mpg', '.mpeg'}

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        log(f"\nLoading Whisper model once for batch processing: {device} / {compute_type} / {args.model}")
        model = WhisperModel(args.model, device=device, compute_type=compute_type)

        processed = 0
        for filename in os.listdir(args.input):
            if not filename.lower().endswith(tuple(video_exts)): continue
            input_path = os.path.join(args.input, filename)
            if not os.path.isfile(input_path): continue
            if "noprof" in filename.lower():
                log(f"Skipping already processed file: {filename}")
                continue

            base, ext = os.path.splitext(filename)
            output_path = os.path.join(args.output, f"{base}-noprof{ext}")

            log(f"\n=== Batch processing [{processed + 1}]: {filename} ===")
            mute_profanity(input_path, output_path, model=model, validate=args.validate, safe=args.safe,
                           whisper_model=args.model, beam_size=args.beam, enhance=args.enhance,
                           quiet=args.quiet, custom_words=args.custom_words, merge=not args.no_merge)
            processed += 1

        log("Batch complete. Releasing model and GPU memory...")
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        log(f"\nBatch processing complete! {processed} video(s) processed.")

    else:
        if not os.path.isfile(args.input):
            log("ERROR: In single-file mode, the input must be a video file.")
            sys.exit(1)
        mute_profanity(args.input, args.output, validate=args.validate, safe=args.safe,
                       whisper_model=args.model, beam_size=args.beam, enhance=args.enhance,
                       quiet=args.quiet, custom_words=args.custom_words, merge=not args.no_merge)