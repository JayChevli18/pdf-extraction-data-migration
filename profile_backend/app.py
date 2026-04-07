"""Optional HTTP API for triggering processing."""

from __future__ import annotations

import logging

from flask import Flask, jsonify

from profile_backend.logging_setup import setup_logging
from profile_backend.pipeline import list_inbox_files, process_inbox, process_one

logger = setup_logging()


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/process")
    def process():
        """Process all files currently in the inbox."""
        before = [str(p) for p in list_inbox_files()]
        records = process_inbox()
        return jsonify(
            {
                "queued": before,
                "processed": len(records),
                "ids": [r.id for r in records],
            }
        )

    @app.post("/process/<path:name>")
    def process_single(name: str):
        """Process one file by name under the inbox directory."""
        from profile_backend.config import INBOX_DIR

        path = (INBOX_DIR / name).resolve()
        if not str(path).startswith(str(INBOX_DIR.resolve())):
            return jsonify({"error": "invalid path"}), 400
        if not path.is_file():
            return jsonify({"error": "not found"}), 404
        rec = process_one(path)
        return jsonify({"id": rec.id, "name": rec.name})

    return app


def main():
    setup_logging()
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
