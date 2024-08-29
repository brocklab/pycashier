paper.pdf: paper.md paper.bib workflow.png
	docker run --rm \
    --volume $$PWD/:/data \
    --user $$(id -u):$$(id -g) \
    --env JOURNAL=joss \
    openjournals/inara

workflow.png: workflow.dot
	dot -Tpng -s300 -o$@ $<
