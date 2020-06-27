import torch,h5py

class UDHR_Dataset(torch.utils.data.Dataset):
    '''dataset = UDHR_Dataset(hdf5filename, sort_order, x, y)
    Creates a pytorch Dataset object for the UDHR corpus.
    hdf5filename: Path to the hdf5 file created by prepare_data.py --hdf5.
    sort_by: if 'melspectrogram', 'phones', or 'text', data are indexed in order of that object's size.
    sort_order: 'increasing' (default), 'decreasing', or None
    '''
    def __init__(self, hdf5filename, sort_by='melspectrogram', sort_order='increasing'):
        self.hdf5filename = hdf5filename
        self.hdf5 = h5py.File(hdf5filename,'r')
        self.idx2phone = self.hdf5['idx2phone'][()]
        self.idx2char = self.hdf5['idx2char'][()]
        
        self.uttids = [ k for k in self.hdf5.keys() if type(self.hdf5[k])==h5py.Group ]
        if sort_by != None and sort_order == 'increasing':
            self.uttids = sorted(self.uttids, key=lambda uttid: self.hdf5[uttid][sort_by].shape[-1])
        elif sort_by != None and sort_order == 'decreasing':
            self.uttids = sorted(self.uttids, key=lambda uttid: -self.hdf5[uttid][sort_by].shape[-1])
        
    def __len__(self):
        '''Get the length of the dataset (# tokens)'''
        return(len(self.uttids))
    
    def __getitem__(self, n):
        '''Return a copy of the requested HDF5 object'''
        return(self.hdf5[self.uttids[n]])
