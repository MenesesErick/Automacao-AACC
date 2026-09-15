import fitz

doc = fitz.open('Tabela_AACC.pdf')
for i in range(len(doc)):
    print(f'--- PAGINA {i+1} ---')
    print(doc[i].get_text())
