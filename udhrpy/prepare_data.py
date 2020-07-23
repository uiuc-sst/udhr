import argparse,os,subprocess,re,sys,glob,unicodedata,wave
import pycountry, librosa, h5py
import numpy as np
from praatio import tgio
from praatio import audioio
from collections import defaultdict
#from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
#from pdfminer.pdfpage import PDFPage
#from pdfminer.converter import TextConverter
#from pdfminer.layout import LAParams

def load_dict_from_txtfile(txtfile):
    x = {}
    with open(txtfile) as f:
        for line in f:
            words = line.rstrip().split()
            if len(words)==0 or line[0]=='#':
                continue
            if len(words)==1:
                x[words[0]] = ''
            else:
                x[words[0]] = ' '.join(words[1:])
    return(x)

def dir_contains_files(targetdir, filelist):
    if not os.path.isdir(targetdir):
        print('Did not find directory %s'%(targetdir))
        return(False)
    for filename in filelist:
        if not os.path.isfile(os.path.join(targetdir,filename)):
            print('Did not find file %s'%(os.path.join(targetdir,filename)))
            return(False)
    return(True)
        
def load_textgrids(TextGridDir, long2iso, lfn):
    tgs = {}
    for filename in long2iso.keys():
        textgridpath = os.path.join(TextGridDir, filename+'.TextGrid')
        if os.path.isfile(textgridpath):
            tg = tgio.openTextgrid(textgridpath)
            if 'seg' not in tg.tierDict:
                raise KeyError('Required key "seg" not found in %s'%(textgridpath))
            tgs[filename] = tg
    if len(tgs)==0:
        raise FileNotFoundError("None of filenames in %s found in %s"%(lfn,TextGridDir))
    return(tgs)

def wget2dir(targetdir, sources):
    '''Use wget to each file in sources to targetdir. Use wget because urllib.request.urlopen.read()
    puts the result into RAM; really, I'd prefer to have the result go directly to disk, 
    which is what wget does.'''
    os.makedirs(targetdir,exist_ok=True)
    for (n,(filename,url)) in enumerate(sources.items()):
        outputfn = os.path.join(targetdir,filename)
        cmd=['wget',url,'-O',outputfn]
        if n%100==0:
            print("%d'th wget command: %s"%(n,' '.join(cmd)))
        subprocess.run(cmd,check=True)

def unzip2dir(targetdir, zipdir, sources):
    '''Use unzip to unzip all source files into targetdir'''
    os.makedirs(targetdir,exist_ok=True)
    for (n,zipfn) in enumerate(sources):
        zippath = os.path.join(zipdir, zipfn)
        cmd=['unzip',zippath,'-d',targetdir]
        if n%100==0:
            print("%d'th unzip command: %s"%(n,' '.join(cmd)))
        subprocess.run(cmd,check=True)

def mp2wav(wavdir, mp3dir):
    os.makedirs(wavdir,exist_ok=True)
    for (n,pathname) in enumerate(glob.glob(os.path.join(mp3dir, '*.mp3'))):
        basename,ext = os.path.splitext(os.path.basename(pathname))
        outputname = os.path.join(wavdir, basename+'.wav')
        cmd=['ffmpeg','-i',pathname,outputname]
        if n%100==0:
            print("%d'th ffmpeg command: %s"%(n,' '.join(cmd)))
        subprocess.run(cmd,check=True)

def segment_audio(audiodir, wavdir, tgs, long2iso):
    print('Segmenting %s from %s to %s'%(str([x for x in tgs.keys()]),wavdir,audiodir))
    outputnames = []
    for (filename,tg) in tgs.items():
        entryList = tg.tierDict['seg'].entryList
        entryList = [ entry for entry in entryList if not entry[2].isspace() ]
        outdir = os.path.join(audiodir,filename)
        os.makedirs(outdir,exist_ok=True)
        inputfile = os.path.join(wavdir, filename+'.wav')
        wavQObj = audioio.WavQueryObj(inputfile)        
        for entry in entryList:
            start, stop, label = entry
            if not label.isnumeric():
                raise RunTimeError('TextGrid %s contains non-numeric label %s'%(filename,label))
            outputname = os.path.join(outdir, '%s_%4.4d.wav'%(filename,int(label)))
            frames = wavQObj.getFrames(start, stop)
            wavQObj.outputModifiedWav(frames, outputname)            
            outputnames.append(outputname)
            
def load_audio(audiodir='exp/audio', iso=None):
    audiopathlist = list(os.path.split(audiodir))
    wavdir = os.path.join(*(audiopathlist[:-1] + ['wav']))
    long2iso = load_dict_from_txtfile('conf/long2iso.txt')
    if iso != None:
        long2iso = { x:long2iso[x] for x in long2iso.keys() if long2iso[x] in iso.split(':') }
    if not dir_contains_files(wavdir, ['%s.wav'%(x) for x in long2iso.keys()]):
        mp3dir = os.path.join(*(audiopathlist[:-1] + ['mp3']))
        if not dir_contains_files(mp3dir, ['%s.mp3'%(x) for x in long2iso.keys()]):
            zipdir = os.path.join(*(audiopathlist[:-1] + ['zip']))
            librivox_sources = load_dict_from_txtfile(os.path.join('conf','librivox_sources.txt'))
            if not dir_contains_files(zipdir, [ x for x in librivox_sources.keys() ]):
                wget2dir(zipdir, librivox_sources)
            unzip2dir(mp3dir, zipdir, librivox_sources)
        mp2wav(wavdir, mp3dir)
    tgs = load_textgrids('conf/TextGrid/segs',long2iso, 'conf/long2iso.txt')    
    segment_audio(audiodir, wavdir, tgs, long2iso)

#def pdf2text(fulltextdir, pdfdir, long2iso):
#    os.makedirs(fulltextdir,exist_ok=True)
#    filenames = set([x for x in long2iso.values()])
#    for filename in filenames:
#        fname = os.path.join(pdfdir, filename+'.pdf')
#        outputfilename = os.path.join(fulltextdir, filename+'.txt')
#        print('Converting %s to %s'%(fname,outputfilename))
#        rsrcmgr = PDFResourceManager(caching=True)        
#        laparams = LAParams()
#        outfp=open(outputfilename,'w')
#        device=TextConverter(rsrcmgr, outfp, laparams=laparams, imagewriter=None)
#        fp=open(fname, 'rb')
#        interpreter = PDFPageInterpreter(rsrcmgr, device)
#        for page in PDFPage.get_pages(fp):
#            interpreter.process_page(page)
#        fp.close()
#        device.close()
#        outfp.close()

# Some text files have phrases that are not read in the corresponding audio.
# This  lists the phrase counts of those files, so we can double-check ---
# any case not listed here might be a mistake.
phrasecounts = {
    'human_rights_un_arz_ef_64kb' : 104,
    'human_rights_un_bal_brc_64kb' : 112,
    'human_rights_un_bug_brc_64kb' : 123,
    'human_rights_un_cat_nv_64kb' : 108,
    'human_rights_un_bra_rljb_64kb' : 106
    }

# Patterns on which to segment text
# Default: Latin period, Chinese period, and semicolon, in parens so split keeps them.
# Czech, Danish: add commas
default_boundary = re.compile('([\.;。])')
boundary = defaultdict(lambda: default_boundary,
                       [('ces',re.compile('([,\.;。])')),('dan',re.compile('([,\.;。])'))])

def segment_text(textdir, fulltextdir, tgs, long2iso):
    os.makedirs(textdir,exist_ok=True)
    for (n,(longfn,iso)) in enumerate(long2iso.items()):
        fulltextfile = os.path.join(fulltextdir, iso+'.txt')
        textfile = os.path.join(textdir, longfn+'.txt')
        if n%10==0:
            print("Segmenting %d'th fulltext %s to %s"%(n,fulltextfile,textfile))
        lines = []
        with open(fulltextfile) as f:
            for (line_num,line) in enumerate(f.readlines()):
                if line_num >= 5 and len(line)>0:   #  Assume header 5 lines long.  Is always true?
                    lines.append( "".join(c for c in line if unicodedata.category(c)[0]!="C"))
        if len(lines)==0:
            continue
        phrases = [lines[0]]
        if len(lines)>1:
            for line in lines[1:]:
                cl = [ x.strip() for x in re.split(boundary[iso],line) if not x.isspace() and len(x)>0 ]
                for i, c in enumerate(cl):
                    if len(c)==0:
                        continue
                    elif re.match(boundary[iso],c):
                        phrases[-1] = phrases[-1]+c
                    elif i==0 and unicodedata.category(c[0])=='Ll' and not re.match(boundary[iso],phrases[-1][-1]):
                        phrases[-1] = phrases[-1]+c
                    else:
                        phrases.append(c)
        phrases = [ p for p in phrases if not p.isspace() and len(p)>0 ]
        if longfn in tgs and len(phrases) != len(tgs[longfn].tierDict['seg'].entryList):
            if longfn not in phrasecounts or len(phrases) != phrasecounts[longfn]:
                print('WARNING: %s.TextGrid=%d segs; %s has %d.'%
                      (longfn, len(tgs[longfn].tierDict['seg'].entryList),textfile,len(phrases)))
        with open(textfile,'w') as f:
            for n, p in enumerate(phrases):
                line = '%s_%4.4d\t%s\n'%(longfn,n+1,p)
                f.write(line)

def load_text(textdir='exp/text', iso=None):
    textpathlist = list(os.path.split(textdir))
    fulltextdir = os.path.join(*(textpathlist[:-1] + ['fulltext']))
    long2iso = load_dict_from_txtfile('conf/long2iso.txt')
    if iso != None:
        long2iso = { x:long2iso[x] for x in long2iso.keys() if long2iso[x] in iso.split(':') }    
    if not dir_contains_files(fulltextdir,['%s.txt'%(x) for x in long2iso.values()]):
        unicode_sources = load_dict_from_txtfile('conf/unicode_sources.txt')
        wget2dir(fulltextdir, unicode_sources)
        #pdfdir = os.path.join(*(textpathlist[:-1] + ['pdf']))
        #united_nations_sources=load_dict_from_txtfile(os.path.join('conf','united_nations_sources.txt'))
        #if not dir_contains_files(pdfdir,[x  for x in united_nations_sources.keys()]):
        #    wget2dir(pdfdir, united_nations_sources)
        #pdf2text(fulltextdir, pdfdir, long2iso)
    tgs = load_textgrids('conf/TextGrid/segs',long2iso, 'conf/long2iso.txt')    
    segment_text(textdir, fulltextdir, tgs, long2iso)

def git_sparse_checkout(g2pdir,subdir):
    origdir=os.getcwd()
    os.makedirs(g2pdir,exist_ok=True)
    os.chdir(g2pdir)
    cmd=['git','init']
    print(' '.join(cmd))
    subprocess.run(cmd,check=True)
    cmd=['git','remote','add','-f','origin','https://github.com/uiuc-sst/g2ps']
    print(' '.join(cmd))
    subprocess.run(cmd,check=True)
    cmd=['git','config','core.sparseCheckout','true']
    print(' '.join(cmd))
    subprocess.run(cmd,check=True)
    cmd=['echo',subdir,'>>','.git/info/sparse-checkout']
    print(' '.join(cmd))
    subprocess.run(cmd,check=True)
    cmd=['git','pull','origin','master']
    print(' '.join(cmd))
    subprocess.run(cmd,check=True)
    os.chdir(origdir)

def load_phones(phonesdir='exp/phones', textdir='exp/text', iso=None):
    os.makedirs(phonesdir,exist_ok=True)
    #if not os.path.isdir(os.path.join('exp/g2ps','models')):
    #    git_sparse_checkout('exp/g2ps','models')
    modelsdir = 'exp/models'
    os.makedirs(modelsdir, exist_ok=True)
    modeldict = load_dict_from_txtfile('conf/iso2model.txt')
    g2ps_source = "http://www.isle.illinois.edu/speech_web_lg/data/g2ps/models/"
    model_urls = { v+".fst":g2ps_source+v+".fst" for v in modeldict.values() }
    if not dir_contains_files(modelsdir, model_urls):
        wget2dir(modelsdir, model_urls)    
    long2iso = load_dict_from_txtfile('conf/long2iso.txt')
    if iso != None:
        long2iso = { x:long2iso[x] for x in long2iso.keys() if long2iso[x] in iso.split(':') }    
    for (n,(longname,iso)) in enumerate(long2iso.items()):
        modelfile = modeldict[iso]+".fst"
        modelpath = os.path.join(modelsdir,modelfile)
        if not os.path.isfile(modelpath):
            raise FileNotFoundError("Missing %s; did %s exist?"%(modelpath,model_urls[modelfile]))
        inputfn = os.path.join(textdir,'%s.txt'%(longname))
        inputlines = []
        try:
            with open(inputfn) as f:
                for line in f:
                    if len(line)>0 and line[0] != '#':
                        inputlines.append(line.split())
        except:
            continue
        if len(inputlines)==0:
            continue
        uniquewords  = set([ w for line in inputlines for w in line[1:] ])
        wordlist=os.path.join(modelsdir,longname+'_wordlist.txt')
        with open(wordlist,'w') as f:
            f.write('\n'.join(uniquewords))
        cmd=['phonetisaurus-g2pfst','--model=%s'%(modelpath),'--wordlist=%s'%(wordlist)]
        if n%100==0:
            print("%d'th phonetisaurus command: %s:"%(n,' '.join(cmd)))
        proc=subprocess.run(cmd,capture_output=True)
        if len(proc.stderr)>0:
            with open(os.path.join(modelsdir,longname+'_stderr.txt'),'wb') as f:
                f.write(proc.stderr)
        if len(proc.stdout)>0:
            prondictfile=os.path.join(modelsdir,longname+'_stdout.txt')
            with open(prondictfile,'wb') as f:
                f.write(proc.stdout)
            prons = load_dict_from_txtfile(prondictfile)
            outputfn = os.path.join(phonesdir,'%s.txt'%(longname))
            with open(outputfn,'w') as outputfp:
                for line in inputlines:
                    outputline = []
                    if len(line) > 1:
                        for w in line[1:]:
                            if w in prons:
                                pron = prons[w].split()
                                if len(pron)>1:
                                    outputline.append(''.join(pron[1:]))
                                else:
                                    continue
                            else:
                                continue
                    outputfp.write(line[0]+'\t'+' '.join(outputline)+'\n')

def create_hdf5(hdf5filename):
    # This section loads the text for each uttid, and creates idx2char and char2idx
    textroot=next(x for x in ('exp/text','text') if os.path.isdir(x))
    textdata = {}
    for (dirpath, dirnames, filenames)  in os.walk(textroot):
        for filename in filenames:
            textdata.update(load_dict_from_txtfile(os.path.join(dirpath,filename)))
    idx2char = ''.join(sorted(set.union(*[set(s) for s in textdata.values()])))
    char2idx = { idx2char[n]:n for n  in range(len(idx2char)) }
    
    # This section loads the phones for each uttid, and creates idx2phone and phone2idx
    phonesroot=next(x for x in ('exp/phones','phones') if os.path.isdir(x))
    phonesdata = {}
    for (dirpath, dirnames, filenames)  in os.walk(phonesroot):
        for filename in filenames:
            phonesdata.update(load_dict_from_txtfile(os.path.join(dirpath,filename)))
    idx2phone = ''.join(sorted(set.union(*[set(s) for s in phonesdata.values()])))
    phone2idx = { idx2phone[n]:n for n  in range(len(idx2phone)) }

    # This section loads the audio pathnames
    audioroot=next(x for x in ('exp/audio','audio') if os.path.isdir(x))
    audiopaths = {}
    for (dirpath, dirnames, filenames)  in os.walk('exp/audio'):
        for filename in filenames:
            (root, ext)  = os.path.splitext(filename)
            if ext=='.wav':
                audiopaths[root] = os.path.join(dirpath, filename)
                
    # This section intersects the keys of the audio, text, and phones
    uttids  = textdata.keys() &  phonesdata.keys() & audiopaths.keys()
    if len(uttids)==0:
        raise FileNotFoundError("%s, %s, %s: no uttids in common"%(audioroot,textroot,phonesroot))

    # This section just finds the ISO code and language name for each utterance
    long2iso = load_dict_from_txtfile('conf/long2iso.txt')
    uttid2langname = {}
    uttid2iso = {}
    for uttid  in uttids:
        longname = re.sub(r'_\d\d\d\d$','',uttid)
        iso_list = long2iso[longname].split('-')
        if len(iso_list)>0 and pycountry.languages.get(alpha_3=iso_list[0]):
            langname = pycountry.languages.get(alpha_3=iso_list[0]).name
        else:
            langname = 'Unknown'
        if len(iso_list)>1 and pycountry.countries.get(alpha_2=iso_list[1]):
            langname = langname + ' - ' + pycountry.countries.get(alpha_2=iso_list[1]).name
        uttid2iso[uttid] = '-'.join(iso_list)
        uttid2langname[uttid] = langname

    # This section converts the audio to melspectrogram, and writes everything to the HDF5 file
    stype=h5py.string_dtype(encoding='utf-8')
    with h5py.File(hdf5filename, 'w') as f:
        f.create_dataset('idx2char', data=idx2char, dtype=stype)
        f.create_dataset('idx2phone', data=idx2phone, dtype=stype)
        for (n,uttid) in enumerate(uttids):
            if n%100 == 0:
                print("Creating %d'th melspectrogram: %s"%(n,uttid))
            g = f.create_group(uttid)
            g.create_dataset('uttid', data=uttid, dtype=stype)
            g.create_dataset('iso639-3-iso3166-1', data=uttid2iso[uttid], dtype=stype)
            g.create_dataset('languagename', data=uttid2langname[uttid], dtype=stype)
            g.create_dataset('text', data=np.array([char2idx[c] for c in textdata[uttid]]))
            g.create_dataset('phones', data=np.array([phone2idx[p] for p in phonesdata[uttid]]))
            (x,fs) = librosa.load(audiopaths[uttid])
            params = {
                'hop_length' : int(fs*0.01),
                'win_length' : int(fs*0.03),
                'window' : 'hamming',
                'center' : False,
                'fmax' : 8000
            }            
            g.create_dataset('melspectrogram', data=librosa.feature.melspectrogram(x,fs,**params))
            g.create_dataset('nsamps',data=len(x),dtype='int')
            g.create_dataset('samprate',data=fs,dtype='int')


###########################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser(
        description='''Prepare the dataset: download original sources, and format them.
        You shouldn't need to run this, unless you have contributed a new TextGrid
        and want to verify that it works.  If so, try --all to download and process
        the original data files.''')
    parser.add_argument('--audio',action='store_true',
                        help='''Use conf/utt2iso.txt and TextGrid to segment exp/wav into exp/audio.
                         ... If all wav files are not in exp/wav, ffmpeg them from exp/mp3.
                         ... If all mp3 files are not in exp/mp3, unzip them from exp/zip.
                         ... If all zip files are not in exp/zip, wget them from librivox.''')
    parser.add_argument('--text',action='store_true',
                        help='''Use conf/utt2iso.txt and TextGrid to convert exp/fulltext into exp/text.
                         ... If all txt files are not in exp/fulltext, pdftotext them from exp/pdf.
                         ... If all pdf files are not in exp/pdf, wget them from United Nations.''')
    parser.add_argument('--phones',action='store_true',
                        help='''Phonetisaurus exp/models to map exp/text to exp/phones.
                         ... If fst.gz are not in exp/models, git clone them from uiuc-sst/g2ps.''')
    parser.add_argument('--hdf5',action='store_true',
                        help='''Create an h5py file exp/UDHR.hdf5 file that contains the entire dataset,
                        including melspectrogram computed from each audio file using librosa.
                        Audio files are sought in exp/audio if it exists, else from audio;
                        likewise for [exp/text, text] and [exp/phones, phones].  So
                        if you want to read from the audio subdirectory, first delete exp/audio.''')
    parser.add_argument('-i','--iso',
                        help='''Process only the specified iso code(s).
                        If you want more than one code, separate them with colons, e.g.,
                        --iso eng-US:eng-GB:por-BR:ace:epo
                        ''')
    parser.add_argument('--all',action='store_true',
                        help='Perform --audio, --text, --phones, --hdf5 in that order.')
    args = parser.parse_args()
    if args.all:
        args.audio=True
        args.text=True
        args.phones=True
        args.hdf5=True
        
    if not args.audio and not args.text and not args.phones and not args.hdf5:
        parser.print_help()
        sys.exit(0)

    if args.audio:
        load_audio('exp/audio', iso=args.iso)

    if args.text:
        load_text('exp/text', iso=args.iso)

    if args.phones:
        load_phones('exp/phones','exp/text', iso=args.iso)

    if args.hdf5:
        create_hdf5('exp/UDHR.hdf5')

