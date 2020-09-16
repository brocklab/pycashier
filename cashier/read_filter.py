import os
import csv

def filter_by_percent(file_in,filter_percent):
    
    filename, file_extension = os.path.splitext(file_in)
    csv_file = '{}.min{}{}'.format(filename,filter_percent,file_extension)
    csv_out = os.path.join('../outs', csv_file)
    total_reads = 0

    with open(file_in, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        for row in spamreader:
            total_reads += float(row[1])

    filter_count =  int(round( total_reads * filter_percent / 100 , 0))
    

    filter_by_count(file_in, filter_count)

def filter_by_count(file_in, filter_count):
    
    filename, file_extension = os.path.splitext(file_in)
    csv_file = '{}.min{}{}'.format(filename,filter_count,file_extension)
    csv_out = os.path.join('../outs', csv_file)

    with open(file_in, 'r') as csv_in:
        with open(csv_out, 'w') as csv_out:
            for line in csv_in:
                linesplit = line.split('\t')
                if int(linesplit[1]) >= filter_count:
                    csv_out.write(u'{}\t{}'.format(*linesplit))

def read_filter(sample,filter_count,filter_percent,quality,ratio,distance,**kwargs):
    
    file_in = '{}.barcodes.q{}.r{}d{}.tsv'.format(sample,quality,ratio,distance)

    if filter_count:
        print('\nremoving sequences with less than {} total occurences'.format(filter_count))
        filter_by_count(file_in,filter_count)
    
    else:
        print('\nremoving sequences with less than {}% of the total reads per sample'.format(filter_percent))
        filter_by_percent(file_in,filter_percent)