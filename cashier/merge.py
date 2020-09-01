import os
import re
import shlex
import subprocess

def merge_single(sample,fastqs,fastqdir,threads,**kwargs):
	keep_output = kwargs['keep_output']
	pear_args = kwargs['pear_args']
	#perform usearch check..
	# if not os.path.isfile(os.path.join(os.getenv('HOME'),'bin/usearch')):
	# 	print("Error! Could not find usearch in ~/bin")
	# 	print("Please download usearch from: https://www.drive5.com/usearch/download.html")
	# 	exit()
	###########################check ~/bin for usearch
	#update the file name collection to sample wide dict with seperate function called in main script and passed to merge.
	print("Beginning work with sample: {}".format(sample))
	
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
		print("oops I didnt find an R1 or R2 file")
		exit()
	
	merged_barcode_fastq = '{}.merged.raw.fastq'.format(sample)
	merged_barcode_file = '{}.merged.raw'.format(sample)

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

		for f in files: 

			old_path = os.path.realpath(os.path.join("../",fastqdir,f))
			new_path = os.path.join(os.path.realpath(os.getcwd()),f)
			os.rename(old_path,new_path)

		print('Merging fastqs')


		#here I would need to switch to using pear as the merging software 
		#command = 'usearch -fastq_mergepairs {} -fastqout {}'.format(files[0], merged_barcode_fastq)
		#also include a thread argument in this call
		command = 'pear -f {} -r {} -o {} -j {} {}'.format(files[0], files[1], merged_barcode_file, threads, pear_args)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		p.wait()

		#remove the extra files made from pear
		if kwargs['keep_output']!=True:
			for f in ['discarded.fastq','unassembled.forward.fastq','unassembled.reverse.fastq']:
				file = '{}.{}'.format(merged_barcode_file,f)
				os.remove(file)

		os.rename(merged_barcode_file + '.assembled.fastq', merged_barcode_fastq)
	else:
		print('Found merged barcode fastq for sample:{}'.format(sample))


def merge(fastqs, fastqdir, cli_args):
        
	if not os.path.exists('mergedfastqs'):
		os.makedirs('mergedfastqs')

	samples=[]
	
	for f in fastqs:

		m=re.search(r'(.+?)\..*R.*\.fastq\.gz',f)
		if m:
			samples.append(m.group(1))
		else:
			print('Failed to obtain sample name from {}'.format(f))
			exit()

	print('Found the following samples:')
	for s in set(samples): print(s)
	print()

	if len(samples)/len(set(samples))!=2:
		print("There should be an R1 and R2 fastq file for each sample.")
		exit()

	os.chdir('mergedfastqs')

	for sample in set(samples):
		
		merge_single(sample,fastqs,fastqdir,cli_args['main']['threads'],**cli_args['merge'])

	print("\nCleaning up single read fastq files.")

	clean_fastqs = os.listdir('.')
	for f in clean_fastqs:
		if "R1" in f or "R2" in f:
			os.remove(f)

	print("All samples have been merged and can be found in mergedfastqs\n")
	exit()