# Language Preference

Reports and chat summaries use **one** primary language, identified by a **BCP-47-like tag** (e.g. `en`, `zh-CN`, `zh-TW`, `ja`, `ko`, `de`, `fr`, `es`, `pt-BR`, `ru`, `ar`, …).

First-class export chrome (TOC/subtitle defaults, CJK fonts) is richest for `en` and Chinese-family tags; other languages still work — the agent writes body prose in that language, and export falls back to English chrome labels unless `_document.json` overrides them.

## Priority (highest first)

1. **Explicit user request** — `--language ja`, “auf Deutsch”, “用日语写”, “en français”, etc.
2. **Existing workspace choice** — `.omr/locale.json` → `language`, or `.omr/report-state.json` → `language` if synthesis already started.
3. **Research-question / materials language** — if the topic and majority of user messages are clearly in one language, follow that.
4. **Timezone preference** — map local IANA timezone → language tag (see below).
5. **OS locale hint** — parse `LANG` / `LC_*` / `LANGUAGE` (e.g. `ja_JP.UTF-8` → `ja`, `pt_BR` → `pt-BR`).
6. **Fallback** — `en`.

Never mix primary prose languages in one report unless the user asked for bilingual.

## Timezone → language (examples)

| Zone | Language |
|------|----------|
| `Asia/Shanghai`, `Asia/Chongqing`, … | `zh-CN` |
| `Asia/Taipei` | `zh-TW` |
| `Asia/Hong_Kong`, `Asia/Macau` | `zh-HK` |
| `Asia/Tokyo` | `ja` |
| `Asia/Seoul` | `ko` |
| `Asia/Bangkok` | `th` |
| `Asia/Ho_Chi_Minh` | `vi` |
| `Asia/Jakarta` | `id` |
| `Asia/Kuala_Lumpur` | `ms` |
| `Asia/Kolkata` | `hi` |
| `Asia/Dubai`, `Asia/Riyadh`, `Africa/Cairo` | `ar` |
| `Europe/Berlin`, `Europe/Vienna` | `de` |
| `Europe/Paris`, `Europe/Brussels` | `fr` |
| `Europe/Madrid`, many LatAm zones | `es` |
| `America/Sao_Paulo` | `pt-BR` |
| `Europe/Lisbon` | `pt-PT` |
| `Europe/Rome` | `it` |
| `Europe/Amsterdam` | `nl` |
| `Europe/Warsaw` | `pl` |
| `Europe/Moscow` | `ru` |
| `Europe/Kyiv` | `uk` |
| `Europe/Istanbul` | `tr` |
| `Europe/London`, `America/New_York`, `Asia/Singapore`, `Australia/Sydney` | `en` |

Full machine map: `python3 scripts/prefer_language.py --list`.

**Do not** infer language from bare offsets (`UTC+8`, `CST`) alone — too ambiguous. Prefer named IANA zones.

## Locale → language

If timezone does not resolve, parse OS locale:

- `zh_CN` / `zh-CN` / `zh_SG` → `zh-CN`
- `zh_TW` → `zh-TW`; `zh_HK` / `zh_MO` → `zh-HK`
- `ja_JP` → `ja`; `ko_KR` → `ko`
- `pt_BR` → `pt-BR`; `pt_PT` → `pt-PT`
- other `ll` / `ll_CC` → normalized tag (`de`, `fr`, `es`, `ru`, …) or well-formed unknown tags kept as-is

## Mechanical helper

```bash
# Print detected tag (e.g. ja, de, zh-CN)
python3 skills/oh-my-research/scripts/prefer_language.py

# Full record
python3 skills/oh-my-research/scripts/prefer_language.py --json

# Override timezone for detection
python3 skills/oh-my-research/scripts/prefer_language.py --timezone Asia/Tokyo --json

# Known timezone map
python3 skills/oh-my-research/scripts/prefer_language.py --list

# Persist into a research workspace (INIT / first synth)
python3 skills/oh-my-research/scripts/prefer_language.py --write-workspace /path/to/workspace

# Explicit override
python3 skills/oh-my-research/scripts/prefer_language.py --language ja
```

## Agent checklist

### INIT

1. Run timezone/locale detection (`prefer_language.py` or equivalent).
2. Write `.omr/locale.json`:

```json
{
  "language": "ja",
  "source": "timezone",
  "timezone": "Asia/Tokyo",
  "detected_at": "2026-08-18T20:00:00+09:00"
}
```

3. Mention the preferred language in the INIT reply (user can override).

### SYNTH / chat

1. Resolve language with the priority list above.
2. Write all public chapters in that language; set `_document.json` chrome strings for TOC/subtitle when not `en`/`zh-*` (so export is not English-only chrome on a non-English body).
3. Pass the same tag to `export_report.py --language <tag>`.
4. For CJK family (`zh-*`, `ja`, `ko`), set the **East Asian** face only in `eastasia` / `pdf_cjk` and keep a real Latin face in `latin` / `pdf_latin`. The exporter binds them separately and renders Latin words inside CJK text (`Gödel`, `DeepSeek-R1`, `·`) with the Latin face; putting a CJK font in `latin` reintroduces broken accents and half-width spacing.
5. Unicode symbols (`→ ⇒ ≥ ✓ ✗ ★ ①`) need no spec field: the exporter embeds a wide-coverage system font for them, since neither standard Latin nor CJK fonts cover the full set.
6. If user later switches language, update `.omr/locale.json` and confirm before rewriting chapters.

### Chat replies

Match the preferred language for status lines and summaries unless the user is clearly writing in another language (mirror that turn; keep report language stable).
