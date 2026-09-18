"""Page-aware layout and table extraction; image interpretation is never invented."""
import pdfplumber
from pypdf import PdfReader

def extract_document(path):
    reader = PdfReader(path)
    if reader.is_encrypted: raise ValueError('Encrypted PDFs are unsupported. Upload an unlocked PDF.')
    if len(reader.pages)>200: raise ValueError('PDF exceeds the 200-page prototype limit.')
    chunks, pages, unsupported = [], [], []
    with pdfplumber.open(path) as pdf:
        for number,page in enumerate(pdf.pages,1):
            text = (page.extract_text(layout=True) or '').strip()
            tables = page.extract_tables()
            headings = []
            sizes = sorted(c.get('size',0) for c in page.chars)
            median = sizes[len(sizes)//2] if sizes else 0
            for word in page.extract_words(extra_attrs=['size']):
                if word.get('size',0)>median*1.2: headings.append(word['text'])
            table_text = []
            for index,table in enumerate(tables,1):
                lines = [' | '.join((cell or '').replace('\n',' ') for cell in row) for row in table if any(row)]
                if lines: table_text.append(f'Table {index} (page {number}):\n'+'\n'.join(lines))
            if len(text)<40 and not table_text: unsupported.append(number)
            else:
                # Preserve layout whitespace within bounded chunks. Tables get their own
                # chunks so column relationships survive retrieval and exact citations.
                lines = text.splitlines(); part=[]; size=0; ordinal=0
                for line in lines:
                    if size+len(line)>2200 and part:
                        chunks.append((number,ordinal,'\n'.join(part)));ordinal+=1;part=[];size=0
                    part.append(line);size+=len(line)
                if part: chunks.append((number,ordinal,'\n'.join(part)));ordinal+=1
                for table in table_text:
                    for start in range(0,len(table),4000):
                        chunks.append((number,ordinal,table[start:start+4000]));ordinal+=1
            pages.append({'page':number,'tables':len(table_text),'images':len(page.images),'heading':' '.join(headings)[:300],'characters':len(text)})
    if not chunks: raise ValueError('No extractable text. Scanned/image-only PDFs need OCR before upload; OCR is not supported.')
    return chunks, {'extractor':'pdfplumber-layout-v1','pages':pages,'unsupported_pages':unsupported,'table_count':sum(p['tables'] for p in pages)}
