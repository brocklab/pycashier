import os
import csv


def convert_to_csv(in_file, out_file):

    for i,line in enumerate(in_file):

        if not line.startswith('@') or in_file[i-1].strip()=='+':
            continue
        seq_id = line.strip()
        sequence = in_file[i+1].strip()
        out_file.write(u'{}\t{}\n'.format(seq_id,sequence))

def fastq_to_csv(in_file, out_file):

    print('transforming barcode fastq into tsv')
    with open(in_file) as f_in:
        with open(out_file, 'w') as f_out:
            convert_to_csv(f_in.readlines(),f_out)

def extract_csv_column(csv_file,column):

    filename, file_extension = os.path.splitext(csv_file)
    tmp_out = '{}.c{}{}'.format(filename,column,file_extension)
    
    with open(csv_file,'r') as csv_in:
        with open(tmp_out,'w') as csv_out:
            for line in csv_in:
                linesplit = line.split('\t')
                csv_out.write(u'{}'.format(linesplit[column-1]))
                              
    return tmp_out
