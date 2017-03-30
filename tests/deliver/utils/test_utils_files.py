from deliver.utils.files import get_mipname

def test_get_mipname():
    assert get_mipname('/mnt/hds/proj/bioinfo/DEMUX/170127_ST-E00198_0198_BHC7NYALXX/Unaligned/Project_515978/Sample_ELH2173A1/HC7NYALXX-l1t11_515978_AACGTGAT_L001_R1_001.fastq.gz') == '1_170127_HC7NYALXX-11_ELH2173A1_AACGTGAT_1.fastq.gz'
    assert get_mipname('/mnt/hds/proj/bioinfo/DEMUX/170127_ST-E00198_0198_BHC7NYALXX/Unaligned/Project_515978/Sample_ELH2173A1/HC7NYALXX-l1t11_Undetermined_AACGTGAT_L001_R1_001.fastq.gz') == '1_170127_HC7NYALXX-11-Undetermined_ELH2173A1_AACGTGAT_1.fastq.gz'
    assert get_mipname('/mnt/hds/proj/bioinfo/DEMUX/170127_D00483_0183_BCAHT8ANXX/Unaligned8/Project_576645/Sample_RNA1460A10_dual10/RNA1460A10_dual10_TCCGGAGA-ATAGAGGC_L001_R1_001.fastq.gz') == '1_170127_CAHT8ANXX_RNA1460A10_TCCGGAGA-ATAGAGGC_1.fastq.gz'
    assert get_mipname('/mnt/hds/proj/bioinfo/DEMUX/170127_D00483_0183_BCAHT8ANXX/Unaligned8/Project_576645/Sample_RNA1460A10_dual10/RNA1460A10_TCCGGAGA-ATAGAGGC_L001_R1_001.fastq.gz') == '1_170127_CAHT8ANXX_RNA1460A10_TCCGGAGA-ATAGAGGC_1.fastq.gz'
