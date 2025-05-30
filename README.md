# poma-senter

[![PyPI version](https://img.shields.io/pypi/v/poma-senter.svg)](https://pypi.org/project/poma-senter/)  
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](LICENSE)

> **Part of the POMA toolkit.** For the complete documentation, see the [organization README](https://github.com/poma-science/.github).

**Stand-alone sentence cleaner & segmenter** for Markdown, `.poma` archives, OCR dumps, etc.  
Ideal whenever you need reliable one-sentence-per-line output.

> **Note:** The package name is `poma-senter` (with dash) while the import name is `poma_senter` (with underscore).

---

## 🌟 Why use poma-senter?

- **One tool – many inputs.**  
  Clean & split raw text, Markdown or OCR dumps.  
- **OCR-friendly**  
  Fixes hyphen-breaks, stray controls, bad line wraps.  
- **Protects code/tables/images**  
  Leaves `<pre>`, tables (`|…|`), image tags, HTML snippets intact.  
- **Lightweight**  
  Zero external dependencies.

> 👉 See how it fits into the full POMA pipeline:  
> [poma-science/.github README](https://github.com/poma-science/.github#quick-start)  
> [Example Workflow](https://github.com/poma-science/.github/blob/main/example/flow.py)

---

## 🚀 Installation

```bash
pip install poma-senter
```

---

## 🏁 Usage

```python
from poma_senter import clean_and_segment_text

raw = "This is line one—broken\nover two lines! And code:\n<pre>foo()</pre>"
print(clean_and_segment_text(raw))
```

```text
This is line one—broken over two lines!
And code:
<pre>foo()</pre>
```

---

## 📦 API

```python
clean_and_segment_text(text: str) -> str
```

* **Input:** any raw string
* **Output:** cleaned text, one sentence per line

---

## 🛠 Tests

```bash
pytest
```

---

## 🤝 Contribute

1. Fork & clone
2. `pip install -e .`
3. Add tests & docs
4. PR!

---

## 📜 License

MPL-2.0 — see [LICENSE](LICENSE)