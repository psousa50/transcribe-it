.PHONY: transcript install eval eval-view eval-clean promptfoo

transcript:
	bash -c 'set -a && source .env && set +a && uv run transcript $(ARGS)'

install:
	uv cache clean transcript-cli
	uv tool install . --force --reinstall

eval:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo eval $(ARGS)'

eval-view:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo view'

eval-clean:
	rm -rf evals/.promptfoo

promptfoo:
	bash -c 'set -a && source .env && set +a && cd evals && promptfoo $(ARGS)'
