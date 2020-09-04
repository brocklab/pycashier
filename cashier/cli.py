import argparse

def get_args():
    parser = argparse.ArgumentParser(
        prog='cashier',
        usage='%(prog)s [-h] fastqdir'
 #       formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("fastqdir",help='directory containing fastqs to process')
    parser.add_argument("-t","--threads", help='number of cpu cores to use (default: %(default)s)',metavar='',default=1)
    
    #extract specific parameters
    extract_parser = parser.add_argument_group(title='extract options')

    extract_parser.add_argument("-e","--error", help='error tolerance supplied to cutadapt (default: %(default)s)',metavar='',default=0.1,type=float)
    extract_parser.add_argument("-bl","--barcode_length",help='integer length of expected barcode (default: %(default)s)', metavar='', type=int, default=20)
    extract_parser.add_argument("-ua","--upstream_adapter",help="5' sequence flanking barcode",metavar='',type=str,default='ATCTTGTGGAAAGGACGAAACACCG')
    extract_parser.add_argument("-da","--downstream_adapter",help="3' sequence flanking barcode region",metavar='',type=str,default='GTTTTAGAGCTAGAAATAGCAAGTT')
    extract_parser.add_argument("-ul","--unlinked_adapters",help='run cutadapt using unlinked adapters',action='store_true')
    extract_parser.add_argument('-q',"--quality", help='minimum PHRED quality to use to filter reads (default: %(default)s)', metavar='',default=30,type=int)
    #extract_parser.add_argument('-eo',"--extract_only",help='run only barcode extraction on raw fastq files',action='store_true')


    cluster_parser = parser.add_argument_group(title='cluster options') 
    cluster_parser.add_argument("-r","--ratio", help='ratio to use for message passing clustering (default: %(default)s)',metavar='',default = 3,type = int)
    cluster_parser.add_argument("-d","--distance", help='levenshtein distance for clustering (default: %(default)s)',metavar='',default = 1, type = int)
    cluster_parser.add_argument("-fc","--filter_count", help='minimum number of reads for post-cluster filtering',metavar='',default=10,type=int)
    #cluster_parser.add_argument("-co","--cluster_only", help='perform only message passage clustering on a list of sequences',action = 'store_true')    

    merge_parser = parser.add_argument_group(title ='merge options')
    merge_parser.add_argument("-m","--merge", help='merge R1 and R2 fastq files using usearch',action='store_true')
    merge_parser.add_argument("-ko","--keep_output", help='keep auxiliary files output by pear in mergefastqs directory',action='store_true')
    merge_parser.add_argument("-pa","--pear_args", help='additional arguements to pass to pear', type=str, default='')
    args=parser.parse_args()
    
    
    return {'main':
            { 
                'fastqdir':args.fastqdir,
                'threads':args.threads,
                'quality':args.quality
            },
            'extract':
            {
                'error_rate' :args.error,
                'upstream_adapter':args.upstream_adapter,
                'downstream_adapter':args.downstream_adapter,
                'barcode_length':args.barcode_length,
                'unlinked_adapters':args.unlinked_adapters
            #    'extract_only':args.extract_only
            },
            'cluster':
            {
                'ratio':args.ratio,
                'distance':args.distance,
                'filter_count':args.filter_count
            #    'cluster_only':args.cluster_only
            },
            'merge':{
                'merge':args.merge,
                'keep_output':args.keep_output,
                'pear_args':args.pear_args
            }
            }