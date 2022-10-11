import argparse
import logging
import os
import sys

_log = logging.getLogger("sd_embeddings_sync")


def main():
    _log.setLevel(logging.INFO)
    _log.addHandler(logging.StreamHandler(stream=sys.stdout))

    parser = argparse.ArgumentParser(
        prog="sd-embeddings-sync-cli", description="Fetch and sync stable-diffusion embeddings in the draconic way.", add_help=True
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-p", "--embeddingspath", help="Set the embedding folder path", dest="embeddings_path")
    group.add_argument("-i", "--imgpath", help="Set the embedding image folder path", dest="img_path")
    group.add_argument("-j", "--jsonpath", help="Set the location to store the repository database", dest="json_path")
    group.add_argument("-nh", "--nohuggingface", help="Disable sync for huggingface", dest="no_hf", action="store_false")
    parser.set_defaults(no_hf=False, embeddings_path="./embeddings", json_path="./embeddings.json", img_path="./embeddings/images")
    parser.add_argument(
        "-l",
        "--log",
        help="level of log messages to display (default: INFO)",
        dest="log_level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
    )
    args = parser.parse_args()
    if "log_level" in args and args.log_level is not None:
        _log.setLevel(getattr(logging, args.log_level))
    try:
        if args.embeddings_path != "./embeddings":
            if os.path.exists(args.embeddings_path) and os.path.isdir(args.embeddings_path):
                print("Stubbed for now")
            else:
                raise ValueError(f"Path: {args.embeddings_path} is not a directory")
        if args.img_path != "./embeddings":
            if os.path.exists(args.img_path) and os.path.isdir(args.img_path):
                print("Stubbed for now")
            else:
                raise ValueError(f"Path: {args.img_path} is not a directory")
        if args.json_path != "./embeddings.json":
            if os.path.exists(args.json_path) and os.path.isfile(args.json_path) and str(args.json_path).endswith(".json"):
                print("Stubbed for now")
            else:
                raise ValueError(f"Path: {args.json_path} is not a valid JSON file")

    except Exception:
        _log.exception("Unhandled exception")
        return 2


if __name__ == "__main__":
    sys.exit(main())
