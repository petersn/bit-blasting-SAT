
all: diagram1.png

diagram1.pdf: diagram1.tex
	pdflatex $<

diagram1.png: diagram1.pdf
	convert -density 500 $< $@

.PHONY: clean
clean:
	rm -f diagram1.png diagram1.pdf diagram1.aux diagram1.log

