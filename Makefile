format:
	@pre-commit run --all-files

run:
	@python3 -m vidmergebot

clean:
	@pyclean vidmergebot
	@rm -rf vidmergebot/*.session vidmergebot/*.session-journal
	@rm -rf vidmergebot/logs
	@rm -rf vidmergebot/downloads
	@rm -rf inputs*
