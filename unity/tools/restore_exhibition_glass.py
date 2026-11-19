"""Restore the exhibition glass material from the locally imported company package."""

from pathlib import Path
import re


def main():
    assets = Path(__file__).resolve().parents[1] / "Assets"
    source = assets / "00_Model/03_Koreazinc/02_Model/Materials/Tank_Glass_01_01.mat"
    target = assets / "Exhibition/Materials/Tank_Glass_Exhibition.mat"
    meta = target.with_suffix(".mat.meta")
    guid = "268ff627f551494ba558f6dfe1248e96"
    if not source.is_file():
        raise SystemExit("Import fac_watertank.unitypackage before restoring the exhibition glass.")

    material = source.read_text(encoding="utf-8")
    for key, value in (
        ("m_Name", "Tank_Glass_Exhibition"),
        ("_EnableBlendModePreserveSpecularLighting", "0"),
        ("_Metallic", "0"),
    ):
        material, count = re.subn(
            rf"(?m)^( +(?:- )?{key}: )[^\n]+$", rf"\g<1>{value}", material,
        )
        if count != 1:
            raise SystemExit(f"Unexpected source material format for {key}. Restore from the original package.")

    if meta.exists() and not re.search(rf"(?m)^guid: {guid}$", meta.read_text(encoding="utf-8")):
        raise SystemExit(f"Different Unity GUID at {meta}. Move the local material and its .meta before retrying.")
    if target.exists() and target.read_text(encoding="utf-8") != material:
        raise SystemExit(f"A different local material exists at {target}. Move it and its .meta before retrying.")

    target.parent.mkdir(parents=True, exist_ok=True)
    if not meta.exists():
        meta.write_text(
            f"fileFormatVersion: 2\nguid: {guid}\nNativeFormatImporter:\n"
            "  externalObjects: {}\n  mainObjectFileID: 11400000\n"
            "  userData:\n  assetBundleName:\n  assetBundleVariant:\n",
            encoding="utf-8",
        )
    if not target.exists():
        target.write_text(material, encoding="utf-8")
    print("Exhibition glass restored with the scene's original GUID.")


if __name__ == "__main__":
    main()
