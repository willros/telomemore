import re
from collections import defaultdict, Counter
import pysam
from pathlib import Path
from typing import Tuple


class GenerateCsvFiles:
    '''Counts telomeres from bam file generated by cell ranger'''
    
    def __init__(self, bam_file: str):
        self.bam = pysam.AlignmentFile(bam_file, 'rb')
        
    def _number_telomers(self, pattern: str, string: str) -> int:
        counts = re.findall(pattern, string)
        return len(counts)

    def _telomere_counts(self, pattern: str) -> Tuple[dict, dict, int]:
        telomeres_cells = defaultdict(int)
        total_reads_cells = defaultdict(int)
        missed_barcodes = 0
        
        for read in self.bam:
            try:
                total_reads_cells[read.get_tag('CB')] += 1 
                # adds the key to the dict and initializes it to 0 
                telomeres_cells[read.get_tag('CB')]
                if self._number_telomers(pattern, read.seq) >= 5:
                    telomeres_cells[read.get_tag('CB')] += 1
            except Exception:
                missed_barcodes += 1

        return telomeres_cells, total_reads_cells, missed_barcodes
    
    def _write_file(self, out_directory: str, pattern: str) -> None:
        telomere_file = Path(out_directory, 'telomere_counts.csv')
        totalreads_file = Path(out_directory, 'total_reads.csv')
        missed_barcods_file = Path(out_directory, 'missed_barcodes.txt')
        
        telomeres_dict, total_dict, missed_barcodes = self._telomere_counts(pattern)
        
        with open(telomere_file, 'a+') as telomere:
            for key, value in telomeres_dict.items():
                print(f'{key},{value}', file=telomere)
                
        with open(totalreads_file, 'a+') as total:
            for key, value in total_dict.items():
                print(f'{key},{value}', file=total)
                
        with open(missed_barcods_file, 'w+') as missed:
            print(f'Number of missed barcodes = {missed_barcodes}', file=missed)
            
    def run_telomere_count(self, out_directory: str, telomere_pattern: str) -> None:
        '''Generetes a csv file with barcode and number of putative telomeres.'''
        
        print('Starting to write file.')
        self._write_file(out_directory, telomere_pattern)
        print('File written.')
        
    def _k_mer_per_read(self, pattern: str) -> Tuple[dict, int]:
        '''Counts number of kmer in each read and stores the number in list.'''
        kmer_counts = []
        exception = 0
        for read in self.bam:
            try:
                counts = self._number_telomers(pattern, read.seq)
                kmer_counts.append(counts)
            except Exception:
                exception += 1
                
        counter = Counter(kmer_counts)
        return counter, exception
    
    def number_kmers(self, out_directory: str, pattern: str) -> None:
        '''Counts number of kmer in each read and writes results to file.'''
        count_file = Path(out_directory) / f'{pattern}_k_mer_counts.csv'
        missed_file = Path(out_directory) / f'{pattern}_missed_reads.txt'
        
        print(f'Searching for {pattern}...')
        counter, exception = self._k_mer_per_read(pattern)
        
        print(f'Writing {pattern} file...')
        with open(count_file, 'a+') as counts:
            for key, value in counter.items():
                print(f'{key},{value}', file=counts)
            
        
        with open(missed_file, 'w+') as missed:
            print(f'Number of sequences that could not be read: {exception}', file=missed)
        
        print(f'{pattern} files written.')