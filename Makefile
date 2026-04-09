.PHONY: auth ingest ingest-slack eval eval-view eval-clean promptfoo

auth:
	bash -c 'set -a && source .env && set +a && uv run transcript auth gmail $(ARGS)'

ingest:
	bash -c 'set -a && source .env && set +a && uv run transcript ingest gmail $(ARGS)'

ingest-slack:
	bash -c 'set -a && source .env && set +a && uv run transcript ingest slack $(ARGS)'

eval:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo eval $(ARGS)'

eval-view:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo view'

eval-clean:
	rm -rf evals/.promptfoo

promptfoo:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo $(ARGS)'
