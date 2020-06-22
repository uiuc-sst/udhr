# Universal Declaration of Human Rights Corpus

The United Nations has a project to acquire public-domain
translations, into as many languages as possible, of the Universal
Declaration of Human Rights (UDHR).  Librivox.org has a project to
acquire readings of the UDHR in as many languages as possible.

The site you are looking at right now exists for the purpose of
segmenting the librivox recordings, into chunks amenable for the
training and testing of automatic speech recognizers and synthesizers,
and then aligning them to the corresponding texts.

## How to use the corpus

Segmented text and phone transcriptions are distributed with the
corpus (in the "text" and "phones" subdirectories, respectively).
Audio is not distributed with the corpus.  To get it, you'll need
to have wget, unzip, ffmpeg, and python >=3.7 installed; then try the
following steps:

```bash
pip install pycountry
pip install pdfminer
pip install praatio
python scripts/prepare_data.py --audio
```

This will create a directory exp, with subdirectories as follows:
* zip contains the zip files, downloaded from librivox
* mp3 contains the mp3, unzipped from the zip files
* wav contains the wav, converted from mp3 using ffmpeg.
* audio contains the segmented wav files.

You can then move audio out of exp, and delete the
rest of exp.

## How to download the original text sources

If you want to download the original source texts from
United Nations, you can use
scripts/prepare_data.py --text to do that.  You'll need to have some
command-line utilities installed; see the script for more details.

If you want to convert the texts into international phonetic alphabet,
using the languagenet G2Ps, you can use scripts/prepare_data.py --phones to do that.
You'll need to have phonetisaurus installed.

The sources themselves are listed in the files in the conf subdirectory.

## How to contribute

1. If the UN doesn't have a written version of the UDHR in your
   language, please consider donating a translation to
   https://www.ohchr.org/EN/UDHR/Pages/SubmissionGuide.aspx.

2. If the UN has a translation in your language, but only in the form
   of an image, with no corresponding unicode text document, please
   consider transcribing the image to text, and donating it to them
   and/or to me. Languages/Dialects in this situation currently
   include Hebrew, Oriya, Tamil, Urdu, Yiddish.

3. If librivox doesn't have an audio recording in your language, please
   consider donating one.  Register for a librivox account at
   https://forum.librivox.org/ucp.php?mode=register, then
   go to https://forum.librivox.org/viewtopic.php?f=60&t=62306 to read.

