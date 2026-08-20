"""Packaging des serveurs générés (archive zip exportable)."""

from __future__ import annotations

import shutil
from pathlib import Path


def pack_server(source_dir: Path, target_zip: Path | None = None) -> Path:
    """Zip le contenu d'un serveur généré.

    Le dossier racine (nom du serveur) est inclus dans l'archive pour une
    extraction propre. Retourne le chemin de l'archive.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Dossier introuvable : {source_dir}")

    target_zip = target_zip or source_dir.parent / f"{source_dir.name}.zip"
    if target_zip.exists():
        target_zip.unlink()
    shutil.make_archive(str(target_zip.with_suffix("")), "zip", source_dir.parent, source_dir.name)
    return target_zip
