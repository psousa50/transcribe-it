.PHONY: auth transcript eval eval-view eval-clean promptfoo

transcript:
	bash -c 'set -a && source .env && set +a && uv run transcript $(ARGS)'

auth:
	bash -c 'set -a && source .env && set +a && uv run transcript auth gmail $(ARGS)'

eval:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo eval $(ARGS)'

eval-view:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo view'

eval-clean:
	rm -rf evals/.promptfoo

promptfoo:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo $(ARGS)'
