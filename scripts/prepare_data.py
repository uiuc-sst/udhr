import argparse,os,subprocess,re,sys,glob,unicodedata
import pycountry
from praatio import tgio
from praatio import audioio
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
    for (filename,url) in sources.items():
        outputfn = os.path.join(targetdir,filename)
        cmd=['wget',url,'-O',outputfn]
        print(' '.join(cmd))
        subprocess.run(cmd,check=True)

def unzip2dir(targetdir, zipdir, sources):
    '''Use unzip to unzip all source files into targetdir'''
    os.makedirs(targetdir,exist_ok=True)
    for zipfn in sources:
        zippath = os.path.join(zipdir, zipfn)
        cmd=['unzip',zippath,'-d',targetdir]
        print(' '.join(cmd))
        subprocess.run(cmd,check=True)

def mp2wav(wavdir, mp3dir):
    print('Converting mp3 in %s to wav in %s'%(mp3dir,wavdir))
    os.makedirs(wavdir,exist_ok=True)
    for pathname in glob.glob(os.path.join(mp3dir, '*.mp3')):
        basename,ext = os.path.splitext(os.path.basename(pathname))
        outputname = os.path.join(wavdir, basename+'.wav')
        cmd=['ffmpeg','-i',pathname,outputname]
        print(' '.join(cmd))
        subprocess.run(cmd,check=True)

def segment_audio(audiodir, wavdir, tgs, long2iso):
    outputnames = []
    print('Segmenting %s from %s to %s'%(str([x for x in tgs.keys()]),wavdir,audiodir))
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
            
def load_audio(audiodir, tgs, long2iso):
    audiopathlist = list(os.path.split(audiodir))
    wavdir = os.path.join(*(audiopathlist[:-1] + ['wav']))
    if not dir_contains_files(wavdir, ['%s.wav'%(x) for x in long2iso.keys()]):
        mp3dir = os.path.join(*(audiopathlist[:-1] + ['mp3']))
        if not dir_contains_files(mp3dir, ['%s.mp3'%(x) for x in long2iso.keys()]):
            zipdir = os.path.join(*(audiopathlist[:-1] + ['zip']))
            librivox_sources = load_dict_from_txtfile(os.path.join('conf','librivox_sources.txt'))
            if not dir_contains_files(zipdir, [ x for x in librivox_sources.keys() ]):
                wget2dir(zipdir, librivox_sources)
            unzip2dir(mp3dir, zipdir, librivox_sources)
        mp2wav(wavdir, mp3dir)
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
            
def segment_text(textdir, fulltextdir, tgs, long2iso):
    os.makedirs(textdir,exist_ok=True)
    for (longfn,iso) in long2iso.items():
        fulltextfile = os.path.join(fulltextdir, iso+'.txt')
        textfile = os.path.join(textdir, longfn+'.txt')
        print('Converting %s to %s'%(fulltextfile,textfile))
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
                period=re.compile('([\.;。])')  # split on periods and semicolons
                cl = [ x.strip() for x in re.split(period,line) if not x.isspace() and len(x)>0 ]
                for i, c in enumerate(cl):
                    if len(c)==0:
                        continue
                    elif re.match(period,c):
                        phrases[-1] = phrases[-1]+c
                    elif i==0 and unicodedata.category(c[0])=='Ll' and not re.match(period,phrases[-1][-1]):
                        phrases[-1] = phrases[-1]+c
                    else:
                        phrases.append(c)
        phrases = [ p for p in phrases if not p.isspace() and len(p)>0 ]
        if longfn in tgs and len(phrases) != len(tgs[longfn].tierDict['seg'].entryList):
            print('WARNING: %s.TextGrid=%d segs; %s has %d.'%
                  (longfn, len(tgs[longfn].tierDict['seg'].entryList),textfile,len(phrases)))
        with open(textfile,'w') as f:
            for n, p in enumerate(phrases):
                line = '%s_%4.4d\t%s\n'%(longfn,n+1,p)
                f.write(line)

def load_text(textdir, tgs, long2iso):
    textpathlist = list(os.path.split(textdir))
    fulltextdir = os.path.join(*(textpathlist[:-1] + ['fulltext']))
    if not dir_contains_files(fulltextdir,['%s.txt'%(x) for x in long2iso.values()]):
        unicode_sources = load_dict_from_txtfile('conf/unicode_sources.txt')
        wget2dir(fulltextdir, unicode_sources)
        #pdfdir = os.path.join(*(textpathlist[:-1] + ['pdf']))
        #united_nations_sources=load_dict_from_txtfile(os.path.join('conf','united_nations_sources.txt'))
        #if not dir_contains_files(pdfdir,[x  for x in united_nations_sources.keys()]):
        #    wget2dir(pdfdir, united_nations_sources)
        #pdf2text(fulltextdir, pdfdir, long2iso)
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

def load_phones(phonesdir, textdir, long2iso, tgs):
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
    for longname,iso in long2iso.items():
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
        print(' '.join(cmd))
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
    parser.add_argument('-i','--iso',
                        help='''Process only the specified iso code''')
    parser.add_argument('--all',action='store_true')
    args = parser.parse_args()
    if args.all:
        args.audio=True
        args.text=True
        args.phones=True
        
    if not args.audio and not args.text and not args.phones:
        parser.print_help()
        sys.exit(0)

    long2iso = load_dict_from_txtfile('conf/long2iso.txt')
    if args.iso != None:
        long2iso = { x:args.iso for x in long2iso.keys() if long2iso[x]==args.iso }
        
    if args.audio:
        tgs = load_textgrids('conf/TextGrid/segs',long2iso, 'conf/long2iso.txt')
        load_audio('exp/audio',tgs,long2iso)

    if args.text:
        tgs = load_textgrids('conf/TextGrid/segs',long2iso, 'conf/long2iso.txt')
        load_text('exp/text',tgs,long2iso)

    if args.phones:
        load_phones('exp/phones','exp/text',long2iso,tgs)
