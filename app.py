from flask import Flask, request, jsonify, render_template # type: ignore
import re
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- Helpers ----------

def _is_header_line(line: str) -> bool:
    """Detect header-ish lines: allow repeated headers, mixed spacing."""
    norm = re.sub(r'\s+', ' ', line.strip().lower())
    if not norm:
        return False
    return ("hands" in norm and "bb/100" in norm) or norm.startswith("keys ")

def _split_tokens(line: str):
    return re.sub(r'\s+', ' ', line.strip()).split()

def _parse_number_token(tok: str):
    """
    Parse tokens like: 123, 12,345, -2.5, 193k, 8.1k, 2.5m, $1,234.
    Returns float value (expanded for k/m), or None if not numeric-ish.
    """
    t = tok.replace(',', '').replace('$', '').strip()
    m = re.fullmatch(r'[+-]?\d+(?:\.\d+)?([kKmM])?', t)
    if not m:
        return None
    val = float(t[:-1]) if m.group(1) else float(t)
    suf = m.group(1).upper() if m.group(1) else None
    if suf == 'K':
        val *= 1_000
    elif suf == 'M':
        val *= 1_000_000
    return val

def _normalize_stake_token(tok: str) -> str:
    """Normalize stake tokens like '100', '1k', '$200' -> '100', '1K', '200'."""
    t = tok.replace('$', '').strip()
    t = re.sub(r'([km])$', lambda m: m.group(1).upper(), t)
    t = re.sub(r'^(\d+)\.0([KM]?)$', r'\1\2', t)
    return t

stake_slash_re = re.compile(
    r'^\$?([0-9]+(?:\.[0-9]+)?(?:[KkMm])?)/\$?([0-9]+(?:\.[0-9]+)?(?:[KkMm])?)$'
)
stake_plain_re = re.compile(r'^\$?\d+(?:\.\d+)?(?:[KkMm])?$')

def _format_bb100(x: float) -> str:
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s

# ---------- Core parser ----------

def parse_summary_block(raw: str) -> str:
    """
    Returns:
      6m {bb/100}bb/100 over {HandsTok} hands
      HU {bb/100}bb/100 over {HandsTok} hands
      --
      {Stake}NL {bb/100}bb/100 over {HandsTok} hands   (only if Hands > 10k)
      {yyyymmdd}
    """
    if not raw or not raw.strip():
        return ""

    sh_line = None
    hu_line = None
    stake_lines = []

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or _is_header_line(line):
            continue

        tokens = _split_tokens(line)
        if not tokens:
            continue

        key_tok = tokens[0]
        rest = tokens[1:]

        # Pull the first three numeric tokens after the key:
        #   1 = Hands, 2 = Win$, 3 = bb/100
        nums = []
        raw_nums = []
        for tok in rest:
            parsed = _parse_number_token(tok)
            if parsed is not None:
                nums.append(parsed)
                raw_nums.append(tok)
                if len(nums) == 3:
                    break

        if len(nums) < 2:
            continue  # need at least Hands and (eventual) bb/100
        hands_val = int(round(nums[0]))  # numeric for threshold
        hands_tok = raw_nums[0]          # preserve original (e.g., "193k")

        # bb/100: prefer the 3rd numeric token
        bb100_val = nums[2] if len(nums) >= 3 else None
        if bb100_val is None:
            # Fallback: first signed/decimal number after the first numeric
            for tok in rest:
                if tok == hands_tok:
                    continue
                t = tok.replace(',', '').replace('$', '')
                if re.fullmatch(r'[+-]?\d+(?:\.\d+)?', t):
                    bb100_val = float(t)
                    break
        if bb100_val is None:
            continue

        # Map key to label
        key_upper = key_tok.upper()
        label = None
        if key_upper == "SH":
            label = "6m"
        elif key_upper == "HU":
            label = "HU"
        else:
            m = stake_slash_re.match(key_tok)  # e.g., 1K/2K
            if m:
                bb = _normalize_stake_token(m.group(2))
                label = f"{bb}NL"
            elif stake_plain_re.match(key_tok):  # e.g., 50, 100, 200, 400
                st = _normalize_stake_token(key_tok)
                label = f"{st}NL"

        if not label:
            continue

        bb100_str = _format_bb100(bb100_val)

        if label == "6m":
            sh_line = f"6m {bb100_str}bb/100 over {hands_tok} hands"
        elif label == "HU":
            hu_line = f"HU {bb100_str}bb/100 over {hands_tok} hands"
        else:
            if hands_val > 10_000:
                stake_lines.append(f"{label} {bb100_str}bb/100 over {hands_tok} hands")

    out = []
    if sh_line:
        out.append(sh_line)
    if hu_line:
        out.append(hu_line)
    if (sh_line or hu_line) and stake_lines:
        out.append("--")  # separator between top block and stakes
    out.extend(stake_lines)

    # Append today's date at the very end (only if there is any output)
    if out:
        out.append("--")  # separator between stakes and dates
        out.append(datetime.now().strftime("%Y%m%d"))

    return "\n".join(out)

# ---------- Flask endpoints ----------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/format", methods=["POST"])
def format_endpoint():
    data = request.get_json(silent=True) or {}
    raw = data.get("text", "")
    result = parse_summary_block(raw)
    return jsonify({"output": result})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5173, debug=True)
