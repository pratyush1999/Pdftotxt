import pytest
from split_pdf import PdfGetPages
import subprocess
import re
PDF = '/home/pratyush1999/Documents/btp/digitalee/src/pdf_to_txt/app/PDFs/Original PDFs/Regtech in Financial Services.pdf'

pgs=PdfGetPages(PDF)

def test_check():
    assert pgs.check([1,2],[1,2]) == 1
    assert pgs.check([1,2],[0,2]) == 1
    assert pgs.check([1,2],[1000,2000]) == 0

def get_output(page):
	command = ['pdftotext', '-f',
	           str(page), '-l', str(page), '-layout', pgs.pdf_file, '-']
	return subprocess.check_output(command).decode('utf8')

def test_clean():
	pgs.output=['abcde','','xyzwer','','gdgwrrgeg']
	l_remov, maxln=pgs.clean(0)
	assert maxln==9 and l_remov[2]==0
	assert l_remov[0]==0 and l_remov[1]==1
	pgs.output=['a','','','xyzwer']
	l_remov, maxln=pgs.clean(1)
	assert l_remov[0]==1 and l_remov[3]==1

def test_no_pages():
	pgs.get_no_pages()
	assert pgs.no_pages==25

def test_check_split():
	pgs.output = get_output(25)
	l_remov, _=pgs.clean(1)
	spl_spce=48
	flag, _, _=pgs.check_split(spl_spce, l_remov)
	assert flag


def test_main():
	#test1
	pgs.output = get_output(24)
	first_col, second_col, _, _ = pgs.main(pgs.output.splitlines(), 1)
	first_first_col, first_second_col, pg1, pg2 = pgs.main(first_col.splitlines(), 0)
	assert not re.search(r'\S', first_second_col) and pg1[-1]==1
	
	#test2
	pgs.output = get_output(25)
	first_col, second_col, _, _ = pgs.main(pgs.output.splitlines(), 1)
	first_first_col, first_second_col, pg1, pg2 = pgs.main(first_col.splitlines(), 0)
	assert re.search(r'\S', first_second_col)
	
	#test3
	pgs.output=['\u2212']
	first_col, second_col, _, _ = pgs.main(pgs.output, 1)
	assert not re.search(r'\S', first_col)	
