# Statname Reformat

Small, no-deps Flask app that reformats a pasted **Statname “Summary”** block into a clean, shareable summary.

- Paste the raw text → click **Format**
- Output shows:
  - `6m {bb/100}bb/100 over {Hands} hands`
  - `HU {bb/100}bb/100 over {Hands} hands`
  - `--`
  - `{Stake}NL {bb/100}bb/100 over {Hands} hands` (only if **Hands > 10,000**)
  - Final line is **today’s date** in `yyyymmdd`
- Rounds `bb/100` to 1 decimal (trims trailing `.0`)
- Understands hands like `193k`, `8.1k`, `2.5m`
- Robust to tabs/spaces and repeated header rows
- Auto-copies the output to your clipboard
- Runs entirely offline

---

## Quick start

### Requirements
- Python 3.10+
- Flask

### Install
```bash
pip install -r requirements.txt
# or
pip install Flask
```

### Run
```bash
python app.py
# then open http://127.0.0.1:5173
```

---

## Usage

1. **Input**: paste the raw “Summary” block from Statname into the left box.
2. Click **Format** (or press **Ctrl+Enter / Cmd+Enter**).
3. **Output**: reformatted lines appear on the right and are auto-copied to your clipboard.

### What it outputs
```
6m {bb/100}bb/100 over {Hands} hands
HU {bb/100}bb/100 over {Hands} hands
--
{Stake}NL {bb/100}bb/100 over {Hands} hands
{yyyymmdd}
```

---

## Example

**Input**
```
NL   201k  57.5  0.8  29  22  2 days ago
Keys Hands Win $ bb/100 VPIP PFR Last online
SH   193k  2.6k  1.9  28  21  2 days ago
HU   8.1k -2.5k -25.8 78  50  4 days ago
Keys Hands Win $ bb/100 VPIP PFR Last online
50   72k   388.6 1    29  23  2 days ago
100  91k   1.3k  1.1  29  22  4 days ago
200  35k   653.5 0.8  31  23  4 days ago
400  2.5k  -2.2k -19.4 29  22  4 days ago
```

**Output**
```
6m 1.9bb/100 over 193k hands
HU -25.8bb/100 over 8.1k hands
--
50NL 1bb/100 over 72k hands
100NL 1.1bb/100 over 91k hands
200NL 0.8bb/100 over 35k hands
YYYYMMDD
```
> Note: `YYYYMMDD` will be your current local date.

---

## Parsing rules (what it does)

- Ignores header rows like: `Keys Hands Win $ bb/100 VPIP PFR Last online`.
- Recognizes:
  - `SH` → prints a `6m ...` line.
  - `HU` → prints a `HU ...` line.
  - Stakes: numeric (`50`, `100`, `200`) or slash (`1K/2K`) → prints `{BB}NL ...` (uses the big blind from the stake).
- `bb/100` is rounded to 1 decimal; trailing `.0` trimmed.
- Hands tokens retain their original text (e.g. `193k`); for stake lines, they are only included when **Hands > 10,000**.
- Adds a `--` separator between the `6m/HU` block and stake lines (if both exist).
- Appends today’s date (`yyyymmdd`) as the last line when there’s any output.

---

## API (optional)

`POST /format`

**Request JSON**
```json
{"text": "SH 193k 2.6k 1.9 28 21 2 days ago"}
```

**Response JSON**
```json
{"output": "6m 1.9bb/100 over 193k hands\nYYYYMMDD"}
```

Example with `curl`:
```bash
curl -X POST http://127.0.0.1:5173/format   -H "Content-Type: application/json"   -d "{"text":"SH 193k 2.6k 1.9 28 21 2 days ago"}"
```

---

## Project structure

```
.
├─ app.py
├─ templates/
│  └─ index.html
└─ static/
   ├─ app.js
   └─ styles.css
```

---

## Configuration

- **Port**: change in `app.py` (the `app.run(..., port=5173)` line).
- **Title**: set in `templates/index.html` (`<title>` and `<h1>` are currently “Statname Reformat”).
- **Clipboard**: uses the browser Clipboard API; requires a user gesture (the **Format** click/shortcut).

---

## Troubleshooting

- **Flask not found**: `pip install Flask` (or `pip install -r requirements.txt`).
- **Port already in use** (common if Vite uses 5173):
  - Change the port in `app.py`, or
  - Stop the other process using the port.
- **Clipboard didn’t copy**: Some setups block clipboard access; the output still appears in the right box—copy manually if needed.

---

## License

MIT — see [LICENSE](LICENSE).
