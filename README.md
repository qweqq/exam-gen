# Introduction

Simple exam pdf generator supporting English and Bulgarian (may work for other languages as well,
but not tested)

# Setup

## Requirements

- python3.4
- texlive

On Ubuntu and Debian you can install texlive like this:

```bash
sudo apt-get install texlive texlive-science texlive-lang-cyrillic

```

# Running the examples

```bash
python3 src/main.py examples/config.xml
```

The above generates .tex files ready to be compiled with pdflatex. For example:

```bash
mkdir -pv out
rm -fv out/*
# for each generated exam .tex file
for e in exam*.tex; do

    # two iterations per exam are required so that the numbering of pages works
    for i in {1..2}; do
    
        # generate pdf files
        TEXINPUTS=$(pwd)/lib: pdflatex -output-directory=$(pwd)/out $e;
    done;
done;
```

# Usage

(TODO)