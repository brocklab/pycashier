import os
import subprocess
import shlex
# import gzip
# import shutil

def merge(sample,fastqs,fastqdir):

	#perform usearch check..
	###########################check ~/bin for usearch
	#change this to make a sample dict that is {'sample':{'R1':R1_file},'sample2':{'R1':R1_file}} make as a standalone function that checks files then returns the dict of them and put in the utils. 
	print(sample)
    #get the read with R1 in in the name. using regex
    #barcode_fastq = '{}.barcode.merged.fastq'.format(sample)

	R1_regex = r""+ re.escape(sample) + "\..*R1.*\.fastq\.gz"
	m = re.search(R1_regex, fastqs)
	if m:
		R1_file = os.path.join('../',fastqdir,m.group(0))
	else:
		print('ERROR! Failed to find the R1 file for sample:{}'.format(sample))

	R2_regex = r""+ re.escape(sample) + "\..*R2.*\.fastq\.gz"
	m = re.search(R2_regex, fastqs)
	if m:
		R2_file = os.path.join('../',fastqdir,m.group(0))
	else:
		print('ERROR! Failed to find the R2 file for sample:{}'.format(sample))	
	merged_barcode_fastq = '{}.merged.raw.fastq'.format(sample)

	files = [R1_file, R2_file]

	if not os.path.isfile(merged_barcode_fastq):

		print('Performing fastq merge on sample: {}\n'.format(sample))
    	#future implementations may use a python based extraction (using gzip) 

		print('Extracting and moving fastqs')

		command = "gunzip -k {} {}".format(R1_file,R2_file)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		p.wait()

		for f in files: 
			old_path = os.path.join("../",fastqdir,f)
			new_path = os.path.join("mergedfastq",f)
			os.rename(old_path,new_path)

		print('Merging fastqs')

		command = 'usearch -fastq_mergepairs {} -fastqout {}'.format(R1_file, merged_barcoded_fastq)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		p.wait()

	else:
		print('Found merged barcode fastq for sample:{}'.format(sample))