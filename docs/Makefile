
all: diagram1.png

diagram1.pdf: diagram1.tex
	pdflatex $<

diagram1.png: diagram1.pdf
	convert -density 300 $< $@

.PHONY: clean
clean:
	rm -f diagram1.png diagram1.pdf diagram1.aux diagram1.log

