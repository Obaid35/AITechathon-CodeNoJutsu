import PyPDF2
import re

with open('pmdu_manual.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    text = ""
    for i in range(len(reader.pages)):
        text += reader.pages[i].extract_text() + "\n"

with open('pdf_output.txt', 'w', encoding='utf-8') as out:
    # Search for duplicates
    out.write("--- DUPLICATE/MULTIPLE COMPLAINTS ---\n")
    for match in re.finditer(r'.{0,100}(?:duplicate|multiple|same complaint).{0,100}', text, re.IGNORECASE | re.DOTALL):
        out.write("..." + match.group(0).replace("\n", " ") + "...\n")

    out.write("\n--- FORWARDING / WRONG DEPARTMENT ---\n")
    for match in re.finditer(r'.{0,100}(?:forward|wrong|misroute|irrelevant|dropped).{0,100}', text, re.IGNORECASE | re.DOTALL):
        out.write("..." + match.group(0).replace("\n", " ") + "...\n")

    out.write("\n--- LANGUAGE / ATTACHMENT ---\n")
    for match in re.finditer(r'.{0,100}(?:language|attach|word|pdf|audio|video).{0,100}', text, re.IGNORECASE | re.DOTALL):
        out.write("..." + match.group(0).replace("\n", " ") + "...\n")
