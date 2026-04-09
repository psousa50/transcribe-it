.PHONY: auth ingest

auth:
	uv run transcript auth gmail $(ARGS)

ingest:
	uv run transcript ingest gmail $(ARGS)
