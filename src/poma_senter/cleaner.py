import re
import unicodedata


###########
# Globals #
###########


END_PUNCT = {".", "!", "?", ":", ";", "。", "！", "？", "؟"}
BLOCK_STARTERS = {"-", "*", "•", "(", ")", "–", "—", "#", ">", "·"}
TAGS_TO_PROTECT = ["table", "pre", "code", "svg", "iframe", "script"]
MAX_WORDS_WITHOUT_SPLIT = 40

PLACEHOLDER_PATTERN = re.compile(r"^#\{\&--[A-Z]+:\d{5}--\&}#$")
MD_LINK_PATTERN = re.compile(r"\[.*?\]\(.*?\)")
MD_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(.*?\)")
MD_TABLE_PATTERN = re.compile(r"^\s*\|.+\|\s*$")
HEADING_PATTERN = re.compile(r"^#{1,6}\s")
# Pattern to match image description delimiters exactly
IMAGE_DESC_PATTERN = re.compile(r"^(START_IMAGE_DESCRIPTION|END_IMAGE_DESCRIPTION)$")
# NOTE: see also IMAGE_DESCRIPTION_START and IMAGE_DESCRIPTION_END in doc2poma
SENTENCE_PATTERNS = [
    re.compile(r"([a-z0-9]+)(\.)(\s+)([A-Z])"),
    re.compile(r"([a-z0-9]+)([!?…])(\s+)([A-Z])"),
    re.compile(r"(,|;|:)\s+"),
    re.compile(r"\s{2,}"),
]
PROTECT_START_PATTERN = re.compile(rf"^\s*<({'|'.join(TAGS_TO_PROTECT)})\b", re.IGNORECASE)
PROTECT_END_PATTERN = re.compile(rf"^\s*</({'|'.join(TAGS_TO_PROTECT)})>", re.IGNORECASE)


##############
# Processing #
##############


def clean_and_segment_text(text: str) -> str:
    """
    Clean and segment text by removing block tags, normalizing and stripping controls,
    fixing OCR hyphenated breaks, normalizing line endings, splitting into paragraph blocks,
    merging lines, splitting overlong lines, and merging punctuation-only lines.

    Args:
        text (str): The input text to be cleaned and segmented.

    Returns:
        str: The cleaned and segmented text.
    """

    try:
        # Remove block tags but preserve content
        lines = text.splitlines()
        in_protect_block = False
        preserved_lines = []
        for line in lines:
            stripped = line.strip()
            if PROTECT_START_PATTERN.match(stripped):
                in_protect_block = True
                continue
            if in_protect_block:
                if PROTECT_END_PATTERN.match(stripped):
                    in_protect_block = False
                    continue
                preserved_lines.append(line)
                continue
            preserved_lines.append(line)
        text = "\n".join(preserved_lines)

        # Normalize and strip controls
        text = unicodedata.normalize("NFC", text)
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")

        # Fix OCR hyphenated breaks
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
        text = re.sub(r"(\w+)-\s+(\w+)", r"\1-\2", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into paragraph blocks
        blocks = re.split(r"\n{2,}", text)
        blocks = [block.strip() for block in blocks if block.strip()]
        cleaned_blocks = []

        for block in blocks:
            # Remove single linebreaks
            block = re.sub(r"\s*\n\s*", " ", block)
            block = re.sub(r"\s+", " ", block).strip()
            if not block:
                continue

            # Adaptive line merging
            words = block.split()
            avg_word_len = sum(map(len, words)) / len(words) if words else 5
            short_line_threshold = avg_word_len * 7
            parts = block.split(". ")

            # Merge lines in a single pass
            merged = []
            buffer = ""
            i = 0

            while i < len(parts):
                line = parts[i].strip()
                if not line:
                    i += 1
                    continue

                # Detect special lines
                if (
                    PLACEHOLDER_PATTERN.match(line)
                    or MD_LINK_PATTERN.search(line)
                    or MD_IMAGE_PATTERN.search(line)
                    or MD_TABLE_PATTERN.match(line)
                    or HEADING_PATTERN.match(line)
                    or IMAGE_DESC_PATTERN.match(line)  # Special handling for image description delimiters
                    or line.isupper()
                    or len(line) < short_line_threshold
                ):
                    if buffer:
                        merged.append(buffer.strip())
                        buffer = ""
                    merged.append(line)
                    i += 1
                    continue

                next_line = parts[i + 1].strip() if i + 1 < len(parts) else ""
                overnext_line = parts[i + 2].strip() if i + 2 < len(parts) else ""

                should_merge = False
                if line and line[-1] not in END_PUNCT:
                    if next_line and next_line[0].islower():
                        should_merge = True
                    elif not next_line and overnext_line and overnext_line[0].islower():
                        should_merge = True
                if next_line and next_line[0] in BLOCK_STARTERS:
                    should_merge = False

                if should_merge:
                    buffer += " " + line
                else:
                    buffer += " " + line
                    merged.append(buffer.strip())
                    buffer = ""
                i += 1

            if buffer:
                merged.append(buffer.strip())

            parts = merged

            # Split overlong lines
            final_sentences = []
            for s in parts:
                words = s.split()
                if len(words) <= MAX_WORDS_WITHOUT_SPLIT:
                    final_sentences.append(s)
                    continue

                chunk = " ".join(words)
                while len(chunk.split()) > MAX_WORDS_WITHOUT_SPLIT:
                    split_idx = None
                    for pattern in SENTENCE_PATTERNS:
                        matches = list(pattern.finditer(chunk))
                        if matches:
                            split_idx = matches[-1].end()
                            break
                    # Avoid near-end splits that leave tiny leftovers
                    if not split_idx or split_idx >= len(chunk) - 10:
                        final_sentences.append(" ".join(chunk.split()[:MAX_WORDS_WITHOUT_SPLIT]))
                        chunk = " ".join(chunk.split()[MAX_WORDS_WITHOUT_SPLIT:])
                    else:
                        final_sentences.append(chunk[:split_idx].strip())
                        chunk = chunk[split_idx:].strip()
                if chunk.strip():
                    final_sentences.append(chunk.strip())

            # Merge punctuation-only lines
            cleaned = []
            for s in final_sentences:
                s = s.strip()
                if not s:
                    continue
                if re.fullmatch(r"[^\w\s]+", s):
                    if cleaned and cleaned[-1][-1] not in END_PUNCT:
                        cleaned[-1] += " " + s
                    else:
                        cleaned.append(s)
                else:
                    cleaned.append(s)

            cleaned_blocks.append("\n".join(cleaned))

        lines = "\n\n".join(cleaned_blocks).split("\n")

        # Merge lines where a line starts with a lowercase/digit and the previous line doesn't end in punctuation
        # Also merge lines that start with non-alphanumeric characters when both neighbors start with alphanumeric characters
        fixed_lines = []
        for i, line in enumerate(lines):
            if (
                line
                and i > 0
                and re.match(r"^[a-zà-ÿ0-9]", line)
                and not re.search(r"[.!?…:;]$", lines[i - 1].strip())
            ):
                fixed_lines[-1] += " " + line.strip()
            elif (
                line
                and i > 0
                and i < len(lines) - 1
                and re.match(r"^[^a-zA-Zà-ÿÀ-Ÿ0-9\s]", line)  # Starts with non-alphanumeric
                and re.match(
                    r"^[a-zA-Zà-ÿÀ-Ÿ0-9]", lines[i - 1].strip()
                )  # Previous line starts with alphanumeric
                and re.match(
                    r"^[a-zA-Zà-ÿÀ-Ÿ0-9]", lines[i + 1].strip()
                )  # Next line starts with alphanumeric
            ):
                fixed_lines[-1] += " " + line.strip()
            else:
                fixed_lines.append(line.strip())
        lines = fixed_lines

        final_output = "\n".join(lines)

        # Avoid infinite loop by marking reruns
        if getattr(clean_and_segment_text, "_second_pass", False):
            return final_output
        else:
            # Mark this run as the second pass
            clean_and_segment_text._second_pass = True
            result = clean_and_segment_text(final_output)
            del clean_and_segment_text._second_pass
            return result

    except Exception as exception:
        raise Exception(f"(poma-senter) ERROR: cleaning and segmenting text failed: {exception}")
