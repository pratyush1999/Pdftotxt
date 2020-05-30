import pytest
from txt_extracter import PdfTxtExtract
import subprocess
import re
PDF = './PDFs/Regtech in Financial Services.pdf'

pgs=PdfTxtExtract(PDF)

def test_check():
    assert pgs.check([1,2],[1,2]) == 1
    assert pgs.check([1,2],[0,2]) == 1
    assert pgs.check([1,2],[1000,2000]) == 0

def test_init_clean():
	line="ghjhb:kj"
	assert not re.search(r':',pgs.init_clean(line))

def test_main():
	#test1
	pgs.output=['abjslknlk']
	fin, _ = pgs.main(pgs.output, [])
	assert fin=='abjslknlk \n'
	#test2
	pgs.output=['\u2212']
	fin, _ = pgs.main(pgs.output, [])
	

if __name__ == '__main__':
	test_main()
