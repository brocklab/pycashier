# requires https://github.com/charmbracelet/vhs
demo.gif: demo.tape fastqs/demo.fastq clean
	@vhs demo.tape

# make a big fastq file for the demo gif
fastqs/demo.fastq: ../tests/data/reference/rawfastqgzs/test.fastq.gz
	@mkdir -p fastqs
	@for i in $$(seq 1000); do zcat -c $< >> $@; done

.PHONY: clean
clean:
	@rm -rf outs pipeline
