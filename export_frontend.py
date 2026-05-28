from pathlib import Path

FRONTEND_DIR = Path("frontend")
OUTPUT_FILE = Path("frontend_export.txt")

EXCLUDED_DIRS = {
    "node_modules",
    "dist",
    "build",
    ".git",
    ".vite",
    ".next",
    "coverage",
}

EXCLUDED_FILES = {
    "package-lock.json",  # puedes quitarlo si quieres incluirlo
}

ALLOWED_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".css",
    ".scss",
    ".html",
    ".md",
    ".env",
    ".example",
    ".config",
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)

    if parts & EXCLUDED_DIRS:
        return True

    if path.name in EXCLUDED_FILES:
        return True

    if path.name.startswith(".env"):
        return True  # evita exportar claves o secretos

    if path.is_file() and path.suffix not in ALLOWED_EXTENSIONS:
        return True

    return False


def build_file_tree(base_dir: Path) -> str:
    lines = []

    for path in sorted(base_dir.rglob("*")):
        if should_skip(path):
            continue

        relative = path.relative_to(base_dir)
        depth = len(relative.parts) - 1
        indent = "  " * depth

        if path.is_dir():
            lines.append(f"{indent}📁 {path.name}/")
        else:
            lines.append(f"{indent}📄 {path.name}")

    return "\n".join(lines)


def export_files(base_dir: Path, output_file: Path) -> None:
    if not base_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta: {base_dir}")

    with output_file.open("w", encoding="utf-8") as output:
        output.write("# FRONTEND EXPORT\n\n")
        output.write("## ESTRUCTURA DE ARCHIVOS\n\n")
        output.write(build_file_tree(base_dir))
        output.write("\n\n")
        output.write("=" * 80)
        output.write("\n\n")

        for path in sorted(base_dir.rglob("*")):
            if path.is_dir() or should_skip(path):
                continue

            relative_path = path.relative_to(base_dir)

            output.write(f"\n\n## ARCHIVO: frontend/{relative_path}\n")
            output.write("-" * 80)
            output.write("\n\n")

            try:
                content = path.read_text(encoding="utf-8")
                output.write(content)
            except UnicodeDecodeError:
                output.write("[Archivo omitido: no es texto legible en UTF-8]")
            except Exception as e:
                output.write(f"[Error leyendo archivo: {e}]")

    print(f"Export creado correctamente: {output_file}")


if __name__ == "__main__":
    export_files(FRONTEND_DIR, OUTPUT_FILE)
