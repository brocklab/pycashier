# make a big fastq file for the demoing
fastqs/sample.fastq: data/reference/rawfastqgzs/test.fastq.gz
	@mkdir -p fastqs
	@for i in $$(seq 1000); do zcat -c $< >> $@; done

sams/sample.sam: data/reference/sams/test.sam
	@mkdir -p sams
	@for i in $$(seq 1000); do cat $< >> $@; done

clean:
	@rm -rf outs pipeline

.PHONY: clean
