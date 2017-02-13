from deliver.utils.fastq import get_lane, is_undetermined

def test_get_lane():
    assert get_lane('HC7NYALXX-l1t11_515978_AACGTGAT_L001_R1_001.fastq.gz') == 1
    assert get_lane('HC7NYALXX-l1t11_515978_AACGTGAT_L016_R1_001.fastq.gz') == 16
    assert get_lane('/mnt/hds/proj/bioinfo/DEMUX/170127_ST-E00198_0198_BHC7NYALXX/Unaligned/Project_515978/Sample_ELH2173A1/HC7NYALXX-l1t11_515978_AACGTGAT_L001_R1_001.fastq.gz') == 1

def test_is_undetermined():
    assert is_undetermined('HC7NYALXX-l1t11_Undetermined_AACGTGAT_L001_R1_001.fastq.gz') == True
    assert is_undetermined('HC7NYALXX-l1t11_515978_AACGTGAT_L001_R1_001.fastq.gz') == False
    assert is_undetermined('/mnt/hds/proj/bioinfo/DEMUX/170127_ST-E00198_0198_BHC7NYALXX/Unaligned/Project_515978/Sample_ELH2173A1/HC7NYALXX-l1t11_Undetermined_AACGTGAT_L001_R1_001_AACGTGAT_L001_R1_001.fastq.gz') == True
    assert is_undetermined('/mnt/hds/proj/bioinfo/DEMUX/170127_ST-E00198_0198_BHC7NYALXX/Unaligned/Project_515978/Sample_ELH2173A1/HC7NYALXX-l1t11_515978_AACGTGAT_L001_R1_001.fastq.gz') == False
