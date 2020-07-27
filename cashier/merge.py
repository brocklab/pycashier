import os
import subprocess
import shlex
import re
# import gzip
# import shutil

def merge(sample,fastqs,fastqdir):

	#perform usearch check..
	###########################check ~/bin for usearch
	#change this to make a sample dict that is {'sample':{'R1':R1_file},'sample2':{'R1':R1_file}} make as a standalone function that checks files then returns the dict of them and put in the utils. 
	print(sample)
    #get the read with R1 in in the name. using regex
    #barcode_fastq = '{}.barcode.merged.fastq'.format(sample)
	print(fastqs)
	for f in fastqs:

		R1_regex = r""+ re.escape(sample) + "\..*R1.*\.fastq\.gz"
		m = re.search(R1_regex, f)
		if m:
			R1_file = m.group(0)
		

		R2_regex = r""+ re.escape(sample) + "\..*R2.*\.fastq\.gz"
		m = re.search(R2_regex, f)
		if m:
			R2_file = m.group(0)

	if R1_file == None or R2_file == None:
		print("oops I didnt find a file")
		exit()

	
	merged_barcode_fastq = '{}.merged.raw.fastq'.format(sample)

	files = [R1_file, R2_file]

	if not os.path.isfile(merged_barcode_fastq):

		print('Performing fastq merge on sample: {}\n'.format(sample))
    	#future implementations may use a python based extraction (using gzip) 

		print('Extracting and moving fastqs')

		command = "gunzip -k {} {}".format(
			os.path.join('../',fastqdir,R1_file),
			os.path.join('../',fastqdir,R2_file)
			)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		p.wait()

		files = [os.path.splitext(f)[0] for f in files] # replace with sample dict of files
		print(fastqdir)
		print(os.path.realpath(os.getcwd()))
		print(os.path.realpath('../fastqs'))
		for f in files: 

			#f = os.path.splitext(f)[0]
			old_path = os.path.realpath(os.path.join("../",fastqdir,f))
			new_path = os.path.join(os.path.realpath(os.getcwd()),f)
			os.rename(old_path,new_path)

		print('Merging fastqs')

		command = 'usearch -fastq_mergepairs {} -fastqout {}'.format(files[0], merged_barcode_fastq)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		p.wait()

	else:
		print('Found merged barcode fastq for sample:{}'.format(sample))