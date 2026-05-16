import re
import shutil
from pathlib import Path

# *** SET THESE PATHS ***
ROOT_DIR = Path(r"R:\full\path\to\L_betruuuuuuuuuuuung")  # big folder
DEST_DIR = Path(r"R:\full\path\to\tmp_erste30")           # destination folder

DEST_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_EXTS = {".xlsx", ".xls", ".xlsm"}

# Folder like "250113_laufende Analyse"
laufende_pattern = re.compile(r"^\d{6}_laufende Analyse$")

# File like "250113_Data_Transport_...new_process.xlsx"
file_pattern = re.compile(
    r"^(?P<date>\d{6})_Data_Transport_.*new_process$",
    re.IGNORECASE,
)


def find_latest_transport_sheet(folder: Path) -> Path | None:
    """
    In a given laufende folder, find files matching
    yymmdd_Data_Transport_...new_process and return the one
    with the latest yymmdd (tie break: modification time).
    """
    candidates = []

    for f in folder.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in EXCEL_EXTS:
            continue

        stem = f.stem
        m = file_pattern.match(stem)
        if not m:
            continue

        date_str = m.group("date")          # yymmdd
        mtime = f.stat().st_mtime           # modification time
        candidates.append((date_str, mtime, f))

    if not candidates:
        return None

    # sort by date, then by modification time (both descending)
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def find_latest_excel_for_mid_folder(mid_folder: Path) -> Path | None:
    """
    For a given mid (strata) folder:

    - recursively find all subfolders named '2025'
      (covers both mid/2025 and mid/sub/2025)
    - inside each 2025, find laufende folders (yymmdd_laufende Analyse)
    - in the latest laufende of that 2025, find the latest transport sheet
    - among all found sheets under this mid folder, return the newest by yymmdd
    """
    # find all folders named exactly '2025' under this mid folder
    year_2025_folders = [p for p in mid_folder.rglob("*") if p.is_dir() and p.name == "2025"]

    best = None  # (date_str, mtime, path)

    for year_folder in year_2025_folders:
        # laufende folders directly under this 2025
        laufende_folders = [
            d for d in year_folder.iterdir()
            if d.is_dir() and laufende_pattern.match(d.name)
        ]
        if not laufende_folders:
            continue

        # latest laufende folder name (yymmdd part ensures lexicographic = chronological)
        laufende_folders.sort(key=lambda d: d.name, reverse=True)
        latest_laufende = laufende_folders[0]

        excel_file = find_latest_transport_sheet(latest_laufende)
        if excel_file is None:
            continue

        m = file_pattern.match(excel_file.stem)
        if not m:
            continue

        date_str = m.group("date")
        mtime = excel_file.stat().st_mtime

        if best is None or (date_str, mtime) > (best[0], best[1]):
            best = (date_str, mtime, excel_file)

    if best is None:
        return None
    return best[2]


def copy_latest_excel_from_mid_folder(mid_folder: Path) -> None:
    """
    For each mid (strata) folder:

    - find its latest Excel via the 2025 / yymmdd_laufende Analyse /
      yymmdd_Data_Transport_...new_process structure
    - copy to DEST_DIR, prefixing with the mid folder name
    """
    excel_file = find_latest_excel_for_mid_folder(mid_folder)

    if excel_file is None:
        print(f"[INFO] No matching Excel file found for {mid_folder}")
        return

    dest_name = f"{mid_folder.name}_{excel_file.name}"
    dest_path = DEST_DIR / dest_name

    # avoid clashes
    counter = 1
    while dest_path.exists():
        stem = excel_file.stem
        suffix = excel_file.suffix
        dest_name = f"{mid_folder.name}_{stem}_{counter}{suffix}"
        dest_path = DEST_DIR / dest_name
        counter += 1

    shutil.copy2(excel_file, dest_path)
    print(f"[OK] Copied from {excel_file} to {dest_path}")


def main() -> None:
    if not ROOT_DIR.is_dir():
        raise RuntimeError(f"Root directory does not exist: {ROOT_DIR}")

    # each direct subfolder of ROOT_DIR is a mid (strata) folder
    for item in ROOT_DIR.iterdir():
        if item.is_dir():
            copy_latest_excel_from_mid_folder(item)


if __name__ == "__main__":
    main()

