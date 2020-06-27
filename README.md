# Universal Declaration of Human Rights Corpus

The United Nations has a project to acquire public domain
translations, into as many languages as possible, of the Universal
Declaration of Human Rights (UDHR).  Librivox.org has a project to
acquire readings of the UDHR in as many languages as possible.

This repository exists for the purpose of
segmenting the librivox recordings, into chunks amenable for the
training and testing of automatic speech recognizers and synthesizers,
and then aligning them to the corresponding texts. 

## How to use the corpus from bash

Segmented text and automatically generated phone transcriptions are distributed with the
corpus (in the "text" and "phones" subdirectories, respectively).
Audio is not distributed with the corpus.  To get it, you'll need
to have wget, unzip, ffmpeg, and python installed; then try the
following steps:

```bash
pip install pycountry praatio librosa h5py
python udhrpy/prepare_data.py --audio
```

This will create a directory exp, with subdirectories:
* zip contains the zip files, downloaded from librivox
* mp3 contains the mp3, unzipped from the zip files
* wav contains the wav, converted from mp3 using ffmpeg.
* audio contains the segmented wav files.

You can then move audio out of exp, and delete the
rest of exp.

## How to use the corpus from python

```python
import udhrpy
udhrpy.load_audio()
udhrpy.create_hdf5('UDHR.hdf5')
dataset=udhrpy.UDHR_Dataset('UDHR.hdf5')
print('Smallest melspectrogram has shape %s'%(str(dataset[0]['melspectrogram'].shape)))
print(' from uttid %s, language = %s'%(dataset[0]['uttid'][()],dataset[0]['languagename'][()]))
print(''.join(dataset.idx2phone[y] for y in dataset[0]['phones'][:])+'\n')
print('Largest melspectrogram has shape %s'%(str(dataset[-1]['melspectrogram'].shape)))
print(' from uttid %s, language = %s'%(dataset[-1]['uttid'][()],dataset[-1]['languagename'][()]))
print(''.join(dataset.idx2phone[y] for y in dataset[-1]['phones'][:])+'\n')
```

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

2. If librivox doesn't have an audio recording in your language,
   please consider donating one.  Register for a librivox account at
   https://forum.librivox.org/ucp.php?mode=register, then mention your
   language ability and your interest on the "newbie forum"
   (https://forum.librivox.org/viewforum.php?f=17).  You can also read
   the text and post your result in the "Short Works" forum
   (https://forum.librivox.org/viewforum.php?f=19), as soon as you've
   completed the "one minute sound check" described in the Newbie
   Guide to Recording
   (https://wiki.librivox.org/index.php?title=Newbie_Guide_to_Recording).


