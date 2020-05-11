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
    #add upstream and downstream adapter
    extract_parser.add_argument("-ua","--upstream_adapter",help="5' sequence flanking barcode",metavar='',type=str,default='ATCTTGTGGAAAGGACGAAACACCG')
    extract_parser.add_argument("-da","--downstream_adapter",help="3' sequence flanking barcode region",metavar='',type=str,default='GTTTTAGAGCTAGAAATAGCAAGTT')
    extract_parser.add_argument("-ul","--unlinked_adapters",help='run cutadapt using unlinked adapters',action='store_true')
    extract_parser.add_argument('-q',"--quality", help='minimum PHRED quality to use to filter reads (default: %(default)s)', metavar='',default=30,type=int)
    
    cluster_parser = parser.add_argument_group(title='cluster options')
    cluster_parser.add_argument("-r","--ratio", help='ratio to use for message passing clustering (default: %(default)s)',metavar='',default = 3,type = int)
    cluster_parser.add_argument("-d","--distance", help='levenshtein distance for clustering (default: %(default)s)',metavar='',default = 1, type = int)
    cluster_parser.add_argument("-m","--minimum", help='minimum number of reads for post-cluster filtering',metavar='',default=10,type=int)    

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
            },
            'cluster':
            {
                'ratio':args.ratio,
                'distance':args.distance,
                'minimum':args.minimum,
            }
            }
