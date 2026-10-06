import ast
from pathlib import Path


def _get_imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_isolation_of_rag_and_web_search():
    backend_app = Path(__file__).parent.parent / "app"

    rag_dir = backend_app / "rag"
    vector_dir = backend_app / "vectorstore"
    web_dir = backend_app / "web_search"

    # 1. RAG and Vectorstore must NOT import web_search
    for p in list(rag_dir.glob("*.py")) + list(vector_dir.glob("*.py")):
        imports = _get_imports(p)
        for imp in imports:
            assert "web_search" not in imp, f"{p} illegally imports {imp}"

    # 2. Web search must NOT import rag, vectorstore, embeddings, ingestion
    # Exception: shared types or prompts if any, but the rule says:
    # `app/web_search/**` must not import `app.rag`, `app.vectorstore`, `app.embeddings`, or `app.ingestion`.
    for p in web_dir.glob("*.py"):
        imports = _get_imports(p)
        for imp in imports:
            assert not any(
                bad in imp
                for bad in ["app.rag", "app.vectorstore", "app.embeddings", "app.ingestion"]
            ), f"{p} illegally imports {imp}"
