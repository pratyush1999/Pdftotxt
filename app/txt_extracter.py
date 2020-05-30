"""Extracts text from pdfs."""
import re
import copy
import string
from split_pdf import PdfGetPages
import nltk.data
import os

LOG_ENABLE = os.environ["DEPLOYED"] if "DEPLOYED" in os.environ else ''

if LOG_ENABLE == "1":
    from logger import Logger
    LOG = Logger(os.getenv('LOGGER_ADDR'))

class PdfTxtExtract():
    """Performs text extraction on pdfs."""

    def __init__(self, pdf_file):
        """Text extracter class.
            pdf_file: Path of the pdf file.
        """
        self.pdf_file = pdf_file
        self.no_pages = 0
        self.pgno = 0
        self.dict_output_list = {}
        self.output = ""
    @classmethod
    def check(self, list1, list2, flag=0):
        """Addon on the table detection function.
            Checks if the 2 lists have similar in similar positions.
            flag: increase in limit on tholerable difference of elements.
        """
        st1 = copy.deepcopy(list1)
        st2 = copy.deepcopy(list2)
        #if the lists have different lengths, remove the positions at the start which differ much
        while len(st2) < len(st1) and abs(st1[0]-st2[0]) > 5:
            del st1[0]
        while len(st1) < len(st2) and abs(st1[0]-st2[0]) > 5:
            del st2[0]
        for i, j in zip(st1, st2):
            if max(i, j)-min(i, j) > 5+flag:
                return False
        return True
    @classmethod
    def init_clean(self, line):
        """Basic cleaning of line.
            line: input line.
        """
        line += '\n'
        line = re.sub(r':', '', line)
        return line
    @classmethod
    def check_roman(self, line):
        """Checks if the first word of the line is a roman numeral."""
        roman_nums=['x','X','v','V','i','I']
        i=0
        fl=1
        if line[i]=='(':
            i+=1
        while i<len(line) and line[i].isalpha():
           if line[i] not in roman_nums:
               fl=0
           i+=1
        return (fl) or (i<=3) #i<=3 also as this simply means the letters were very small in number and were alphabets.
    @classmethod
    def last_word(self, line):
        """Checks if the last word is a possible end word of a line."""
        #non_ends: list of words which can not be end of a line.
        non_ends=['the', 'or', 'and', 'by', 'with', 'of', 'in', 'for', 'your', 'under', 'to', 'very','/','-', 'Global']
        line=line.rstrip().lstrip()
        i1 = len(line)-1
        i2 = len(line)-1
        last_letter=line[-1].lstrip().rstrip()
        if len(line)>=2 and line[-2].lstrip().rstrip()=='/' and last_letter=='-':
            return 1
        if last_letter in non_ends:
            return 0
        while i1>0 and not line[i1].isalpha():
            i1 -= 1
            i2 -= 1
        while i2>0 and line[i2].isalpha():
            i2 -= 1
        if not line[i2].isalpha():
            i2 += 1
        last_word=line[i2:i1+1].lstrip().rstrip().lower()
        return not last_word in non_ends
    def detect_table(self, l_table, lines_removed, maxx):
        """Table detection.
            l_table: candidate lines of table.
            lines_removed: the dictionary of removed line indices.
            maxx: max length of line.
        """
        #if a table line's starts(defined in later function) is similar enough to the line before, the starting line of 
        # the table block, the line to the before of the previous line, then the line is a part of the same table block.
        i = 1
        while i < len(l_table):
            j = i
            if len(l_table[i][0]) == 1:
                i += 1
                continue
            tble_f = 0
            while j < len(l_table) and tble_f==0 and (self.check(l_table[j][0], l_table[i][0]) or
                                        self.check(l_table[i][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-1][0]) or
                                        self.check(l_table[j-1][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-2][0]) or
                                        self.check(l_table[j-2][0], l_table[j][0])):
                if len(l_table[j][0]) == 1 and l_table[j][0][0] <= 10 and \
                        l_table[j][2][0]-l_table[j][0][0] >= 0.6*maxx:#if a table line is too long and has
                    tble_f = 1                                         #only 1 element in starts, it implies it is a whole line.
                j += 1                                                 #so break this loop.
                lines_removed[l_table[j-1][3]] = 5
            if j == i+1 and tble_f == 0: #only if the last line was different from the first line, go to the next table block.
                i = j                    
            while j < len(l_table) and (self.check(l_table[j][0], l_table[i][0]) or
                                        self.check(l_table[i][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-1][0]) or
                                        self.check(l_table[j-1][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-2][0]) or
                                        self.check(l_table[j-2][0], l_table[j][0])):
                j += 1
                lines_removed[l_table[j-1][3]] = 6
            i = j
        return lines_removed
    def final_lines(self, lines_removed, pg_ends, empty):
        """Returns the final parsed lines.
            lines_removed: the dictionary of removed line indices.
            pg_ends: boolean flag for each line representing if the line is last line of some page.
            empty: boolean flag for each line representing if the line is empty.
        """
        final_lines = ""
        line_hyphen = 1
        bullets = ['-']
        line_end = [':', ',', '.', ';']
        pg_ends_ret = []  # boolean values signifying if the line is the last line of the page
        output = self.output
        removed_lines = ""
        for line_i, line in enumerate(output, 1):
            if line_i not in lines_removed:
                if pg_ends:
                    pg_ends_ret.append(pg_ends[line_i-1])
                line = line.rstrip()
                line = line.lstrip()
                line = re.sub(r'^(?<=[0-9])\s', '.', line) #remove line numbers.
                if (line.isupper() or (not re.search(r'[a-zA-Z]', line))) \
                        and (line[-1] not in line_end): #add full stops at the end of lines which are incomplete or all caps
                    line += '.'                         #and don't already have a line end character at their end.
                line = re.sub(r'\u2013', ':', line)
                line = re.sub(r';', '.', line)
                if len(line) >= 2 and line[0].isalpha() and line[1] == ')':
                    line = line[0]+'.'+line[2:]     #replace 1) with 1.
                #replace - with numbered list if - represents a list of points.
                if line and line[0] == '-':
                    next_ind = 1
                    if len(line) >= 2 and line[1] == '-':
                        next_ind = 2
                    line = str(line_hyphen)+'.'+line[next_ind:]
                    line_hyphen += 1
                elif line and line_i < len(output) and (len(line) <= 2 or line[-2] in line_end)\
                        and self.init_clean(output[line_i]) not in bullets: #reinitialise the line_hyphen counter if the line
                    line_hyphen = 1                                          #doesn't have a - for listing.
                line = line.rstrip()
                #Add full stop at the end of lines which have last character within reasonable limits of the next line
                #, don't already have some punctuation at the end, the first character of next line is capital,
                #and the last word of the line is not a non-ending word.
                if line_i < len(output) and \
                    (re.search(r'^\s*[A-Z]', self.init_clean(output[line_i]))) \
                    and (line[-1] not in line_end and self.last_word(line))\
                    and (len(line) <= len(self.init_clean(output[line_i]))-10 or
                         len(line) >= len(self.init_clean(output[line_i]))-10):
                    line += "."
                #Add full stop at the end of lines which have list numbering or roman numeral for numbering in the next line
                #and don't already have some punctuation at the end.
                #Also add full stop if the next line was non empty but has been removed .
                if line_i < len(output) and \
                    (re.search(r'^[\(]?\w+[\.\)]', self.init_clean(output[line_i])) and self.check_roman(output[line_i])) \
                        and (line[-1] not in line_end):
                    line += "."
                elif line_i < len(output) and (line_i+1 in lines_removed and not empty[line_i+1]) and (line[-1] not in line_end) \
                    and self.last_word(line):
                    line += '.'
                final_lines += line
                final_lines += ' '
                final_lines += '\n'
            #if the line prior and to the next have been removed, removed the intermediary 1 line as well.
            elif (line_i in lines_removed) and (line_i+2 in lines_removed):
                lines_removed[line_i+1]=1
            elif line_i in lines_removed:
                removed_lines += line
        return final_lines, pg_ends_ret, removed_lines

    def main(self, output, pg_ends):
        """Returns the clean text.
        output: input text
        pg_ends: boolean flag for each line representing if the line is last line of some page.
        """
        self.output = output
        lines_removed = {}  # lines and line indices which are removed from input
        l_table = []  # stores lines which are part of table
        maxx = 0  # stores the max length of line
        empty = []  # stores  boolean values signifying if the line is empty
        empty.append(0)
        all_starts = []
        all_ends = []
        for line in output:
            starts, ends, e = PdfGetPages.preprocess(line, 1)
            all_starts.append(starts)
            all_ends.append(ends)
            empty.append(e)
        empty.append(1)
           #starts(index of first character of each segment separated by > = 2 spaces)
            #ends(index of last character of each segment separated by > = 2 spaces)
        for line_i, line in enumerate(output, 1):
            line += '\n'
            line = re.sub(r':', '', line)
            #for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            # stores the index of first character of each segment separated by >=2 space character)
            starts = all_starts[line_i-1]
            # stores the index of last character of each segment separated by >=2 space character)
            ends = all_ends[line_i-1]
            if ends:
                maxx = max(maxx, max(ends))
            #if a line is empty, remove it.
            if len(starts) < 1:
                lines_removed[line_i] = 20
                continue
            #if a line has more than one element in starts , it is a cnadidate for table line.
            #if the line has just 1 element in starts and it is very small, this line is very small and hence just move on.
            #if a line has more than 2 elements in starts, it is highly likely to be a table line and hence directly remove it.
            if len(starts) == 1 and ends[0]-starts[0] <= 2:
                pass
            elif len(starts) >= 2:
                l_table.append([starts, line, ends, line_i])
                if len(starts)>=3:
                    lines_removed[line_i]=22
            #if the line has just 1 segment if delimited by double space, this means it is a whole line and not 2 lines of
            #separate columns. For such lines, if the next line is also whole and 2 lines previous to the current are empty 
            #and the next line after this block of 2 lines is empty, this implies this block of 2 lines is likely to be an image
            #caption as normal lines wouldn't be separated from the other text by 2 empty lines. Same logic would apply if the block
            #of 2 lines is separated by 2 lines at the bottom and 1 line at the top.
            #But if these lines are the last lines of some page, they are less likely to be image caption and hence don't remove them.
            if line_i >= 2 and line_i+3 < len(empty) and \
                    (len(starts) == 1) and len(all_starts[line_i]) == 1 \
                    and ((empty[line_i-1] == 1
                          and empty[line_i-2] == 1 and empty[line_i+2] == 1) or
                         (empty[line_i-1] == 1 and empty[line_i+2] == 1 and
                          empty[line_i+3] == 1)):
                if pg_ends and pg_ends[line_i-1] == 0 and pg_ends[line_i] == 0:
                    lines_removed[line_i] = 3
                    lines_removed[line_i+1] = 3  # for hadling image caption
            if line_i >= 2 and line_i+2 < len(empty) and \
                len(starts) == 1 and ((empty[line_i-1] == 1 and empty[line_i-2] == 1 and
                                       empty[line_i+1] == 1) or
                                      (empty[line_i-1] == 1 and empty[line_i+1] == 1 \
                                       and empty[line_i+2] == 1)):
                if pg_ends and pg_ends and pg_ends[line_i-1] == 0:
                    lines_removed[line_i] = 4  # for hadling image caption
        lines_removed=self.detect_table(l_table, lines_removed, maxx)
        final_lines, pg_ends_ret, removed_lines = self.final_lines(lines_removed, pg_ends, empty)
        return final_lines, pg_ends_ret, removed_lines
    @classmethod 
    def check_url(self, line):
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        return re.search(regex, line)
    @classmethod
    def del_broken_l(self, final_output, output):
        """Removes broken lines from text.
           output: input text.
           final_output: processed text.
        """
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        final_output_list = tokenizer.tokenize(final_output)#list of sentences in final output.
        output_list = tokenizer.tokenize(output)#list of sentences in output.
        #convert list to dictionary for fast access.
        dict_output_list = {}
        for item in output_list:
            if item not in dict_output_list:
                dict_output_list[item] = 1
            else:
                dict_output_list[item] += 1
        dict_final_output_list = {}
        for item in final_output_list:
            if item not in dict_final_output_list:
                dict_final_output_list[item] = 1
            else:
                dict_final_output_list[item] += 1
        final_output = ""
        removed_lines = ""
        #include a sentence only if it is present in both the final list and intial list and has reasonable no of words
        #ad has first letter captial.
        for line in final_output_list:
            if line in dict_output_list and len(line.split())>=5 and len(line.split())<60 and re.search(r'[A-Z]', line[0])\
             and dict_final_output_list[line]==1 and not self.check_url(line):
                line = re.sub(r'\u2014', '-', line)
                line = re.sub(r'\u201c', '"', line)
                line = re.sub(r'\u201d', '"', line)
                line = re.sub(r'\u2019', "'", line)
                line = re.sub(f'[^{re.escape(string.printable)}]', '', line)#remove non printable characters in the line.
                final_output += line
                final_output += ' '
            else:
                removed_lines += line
        return final_output, removed_lines
    def extract_text(self):
        """Caller function for calling the main function."""
        pdftotxt_extract = PdfGetPages(self.pdf_file)
        output, pg_ends = pdftotxt_extract.extract_text()
        output = re.sub(r'(?<=[a-z])\.[0-9]+', '.', output)#remove number superscripts.
        output = re.sub(r'(?<=\s{5})[0-9]+(?=\s)','', output)#remove single numbers separated by many spaces from any text
        output = re.sub(r'(?<=\s)[0-9]+(?=\s{7})','', output)#remove single numbers separated by many spaces from any text
        output = re.sub(r'\u2212', '-', output)
        output = re.sub(r'\u2022', '-', output)
        removed_lines = ""
        final_output, pg_ends, remov_l = self.main(output.splitlines(), pg_ends)
        removed_lines += remov_l
        final_output, _ , remov_l = self.main(
            final_output.splitlines(), pg_ends)
        removed_lines += remov_l
        final_output = re.sub(r' \. ', '   ', final_output)
        final_output = re.sub(r'\n', '', final_output)
        final_output = re.sub(r'\. \.', '.', final_output)
        final_output = re.sub(r'[ \n]+',' ', final_output)
        output = re.sub(r'[ \n]+',' ', output)
        final_output, remov_l = self.del_broken_l(final_output, output)#remove non broken lines.
        removed_lines += remov_l
        if LOG_ENABLE == "1":
            LOG.error('pdf_to_txt', 'POST', 'NULL', 'NULL', removed_lines)
        return final_output


if __name__ == '__main__':
    # PDF = '/home/pratyush1999/Documents/btp/large.pdf'
    PDF = '/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/final_docs/docs/little_error/docs/good/Wealth-Management-in-India-Challenges-and-Strategies.pdf'
    Pdftxt_Extract = PdfTxtExtract(PDF)
    #Pdftxt_Extract.extract_text()
    print(Pdftxt_Extract.extract_text())
    #print("{\"content\":\"", Pdftxt_Extract.extract_text(), "\" , \"summary_percentage\": 100}")
    # output   = subprocess.check_output(command).decode('utf8')
    # print(output)