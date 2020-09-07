import os
import csv
#def post_clustering_min(file_in,minimum):
    # print('Removing sequences with less than {} reads'.format(minimum))
    
    # filename, file_extension = os.path.splitext(file_in)
    # csv_file = '{}.min{}{}'.format(filename,minimum,file_extension)

    # csv_out = os.path.join('../outs', csv_file)

    # with open(file_in, 'r') as csv_in:
    #     with open(csv_out, 'w') as csv_out:
    #         for line in csv_in:
    #             linesplit = line.split('\t')
    #             if int(linesplit[1]) >= minimum:
    #                 csv_out.write(u'{}\t{}'.format(*linesplit))


def filter_percent(file_in,minimum_percent):
    # fix this
    print('Removing sequences with less than {}% of total reads for a sample'.format(minimum_percent))
    
    filename, file_extension = os.path.splitext(file_in)
    csv_file = '{}.min{}{}'.format(filename,minimum_percent,file_extension)
    csv_out = os.path.join('../outs', csv_file)

    with open(file_in, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        for row in spamreader:
            total_reads += float(row[1])

    minimum_read_count = total_reads * minimum_percent / 100

    filter_count(file_in, minimum_read_count)


def filter_count(file_in, minimum_read_count):
    
    filename, file_extension = os.path.splitext(file_in)
    csv_file = '{}.min{}{}'.format(filename,minimum_read_count,file_extension)
    csv_out = os.path.join('../outs', csv_file)

    with open(file_in, 'r') as csv_in:
        with open(csv_out, 'w') as csv_out:
            for line in csv_in:
                linesplit = line.split('\t')
                if int(linesplit[1]) >= minimum:
                    csv_out.write(u'{}\t{}'.format(*linesplit))
