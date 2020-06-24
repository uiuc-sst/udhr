# Universal Declaration of Human Rights Corpus

The United Nations has a project to acquire public domain
translations, into as many languages as possible, of the Universal
Declaration of Human Rights (UDHR).  Librivox.org has a project to
acquire readings of the UDHR in as many languages as possible.

This repository exists for the purpose of
segmenting the librivox recordings, into chunks amenable for the
training and testing of automatic speech recognizers and synthesizers,
and then aligning them to the corresponding texts. 

## How to use the corpus

Segmented text and automatically generated phone transcriptions are distributed with the
corpus (in the "text" and "phones" subdirectories, respectively).
Audio is not distributed with the corpus.  To get it, you'll need
to have wget, unzip, ffmpeg, and python installed; then try the
following steps:

```bash
pip install pycountry praatio
python scripts/prepare_data.py --audio
```

This will create a directory exp, with subdirectories:
* zip contains the zip files, downloaded from librivox
* mp3 contains the mp3, unzipped from the zip files
* wav contains the wav, converted from mp3 using ffmpeg.
* audio contains the segmented wav files.

You can then move audio out of exp, and delete the
rest of exp.

## How to download the original text sources

If you want to download the original source texts from
the UDHR in Unicode project, do this:
```bash
python scripts/prepare_data.py --text
```

To convert the texts into international phonetic alphabet,
using the languagenet G2Ps, install
[https://github.com/AdolfVonKleist/Phonetisaurus](Phonetisaurus).
Then do:
```bash
python scripts/prepare_data.py --phones
```
The source URLs are listed in the files in the conf subdirectory.

## How to contribute

1. If the UDHR in Unicode project (https://www.unicode.org/udhr/)
   doesn't yet have text of the UDHR in your  language, please
   donate a translation at https://www.unicode.org/udhr/contributing.html.

2. If librivox doesn't have an audio recording in your language, please
   consider donating one.  Register for a librivox account at
   https://forum.librivox.org/ucp.php?mode=register, then
   mention your language ability on the "newbie forum,"
   or search "Universal Declaration of Human Rights."

