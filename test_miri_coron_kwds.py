#import pytest
import yaml
from pathlib import Path
import pandas as pd
from astropy.io import fits

# helper function for printing in columns
def print_columns(data, ncols=3):
    if len(data) == 0:
        return
    # convert to strings find the lenght of the longest element
    data_str = list(map(str, data))
    fill = max(map(len, data_str))+3
    # zip the data into columns
    data_cols = [data_str[i::ncols] for i in range(ncols)]
    # make them all the same length to avoid truncation
    max_len = max(map(len, data_cols))
    for col in data_cols:
        while len(col) < max_len:
            col.append('')
    data_cols = list(zip(*data_cols))
    # print
    for row in data_cols:
        width = ' '*fill
        print(f''.join(f"{i:>{fill}}" for i in row))

# Create a test class that gets initialized with a list of data files to test; then the test functions are parameterized using those files
class TestKwds(object):

    def __init__(self, list_of_files):
        """
        Initialize the class with a list of files
        """
        # make sure the input is a list
        if isinstance(list_of_files, str):
            list_of_files = [list_of_files]
        # store all the files you want to test
        self.mirisim_files = list_of_files
        # load the reference list of expected keywords
        self.ref_kwd_file = str(Path(f"{__file__}").parent / "all_coron_kwds.json")
        self.ref_kwds = self.miri_coron_kwds()

        # change this active_file to test a new file
        self.__active_file = list_of_files[0]
        # this gets automatically updated when you change active_file
        self.__active_headers = self.load_headers_from_file(self.active_file)

    def miri_coron_kwds(self):
        """
        Load all the expected keywords as a DataFrame for sorting and grouping
        Columns are the schema name for the category, index is the ASDF name
        FITS keyword names are in the column 'fits_keyword'
        """
        with open(self.ref_kwd_file, 'r') as ff:
            all_kwds = yaml.load(ff, yaml.SafeLoader)
        all_kwds = pd.DataFrame(all_kwds).T
        # some cleaning
        # replace empty strings in 'enum' with pd.NA
        all_kwds.loc[all_kwds['enum'] == '', 'enum'] = pd.NA
        return all_kwds


    def load_headers_from_file(self, file):
        """
        Get a fits file path. Return a dictionary where each key is a header
        name and the entries are the headers
        """
        hdrs = {}
        with fits.open(file, 'readonly') as hdulist:
            for i, hdu in enumerate(hdulist):
                if i == 0:
                    hdrs['PRIMARY'] = hdu.header.copy()
                else:
                    hdrs[hdu.header['EXTNAME']]= hdu.header.copy()
        return hdrs


    @property
    def active_file(self):
        return self.__active_file
    @active_file.setter
    def active_file(self, newval):
        self.__active_file = newval
        print("Active file changed; loading new headers")
        self.active_headers = self.load_headers_from_file(self.__active_file)

    @property
    def active_headers(self):
        return self.__active_headers
    @active_headers.setter
    def active_headers(self, newval):
        self.__active_headers = newval

    def get_ref_kwds_for_header(self, hdu_name):
        """For a header, pull out the keywords that should be in it"""
        ref_kwds = self.ref_kwds.query('fits_hdu == @hdu_name')['fits_keyword']
        return ref_kwds

    def test_kwds_exist(self, hdu_name):
        """
        Test a header to see which keywords do and do not exist
        """
        ref_kwds = self.get_ref_kwds_for_header(hdu_name)
        if len(ref_kwds) == 0:
            print(f"No keywords expected for {hdu_name} HDU")
            return
        test_hdr = self.active_headers[hdu_name]
        kwds_exist = ref_kwds.apply(lambda x: x in test_hdr.keys())
        kwds_present = ref_kwds[kwds_exist[kwds_exist].index]
        kwds_missing = ref_kwds[kwds_exist[~kwds_exist].index]

        # summarize results
        print(f"{len(kwds_present)}/{len(kwds_exist)} expected keywords were found.")
        print("The following keywords *do* exist:")
        print_columns(kwds_present, ncols=4)
        print("")
        print("The following keywords *do not* exist:")
        print_columns(kwds_present, ncols=4)

    def test_all_headers_kwds_exist(self):
        for k in self.active_headers.keys():
            print(f"Testing {k}")
            self.test_kwds_exist(k)
            print("\n")
    
    def test_kwd_enum_values(self, hdu_name):
        """
        For the keywords that are actually found in the MIRISim data,
        and whose allowed values are an enumerated list,
        test that the value found is allowed
        """
        # get the reference keywords
        # if a keyword is not enumerated, it's NaN, so drop those
        bool_idx = (self.ref_kwds['fits_hdu'] == hdu_name) & (~self.ref_kwds['enum'].isna())
        enum_kwds = self.ref_kwds[bool_idx].set_index('fits_keyword', drop=False).copy()
        # get the mirisim kewords
        mirisim_kwds = self.active_headers[hdu_name]
        tested, good, bad = [], [], []
        for k, v in mirisim_kwds.items():
            if k in enum_kwds.index:
                tested.append(k)
                try:
                    assert(v in enum_kwds['enum'].loc[k])
                except AssertionError:
                    bad.append(k)
                else:
                    good.append(k)
        # summarize test results
        print(f"{len(tested)} keywords tested")
        if len(good) > 0:
            print(f"{len(good)}/{len(tested)} keywords are OK: ")
            print_columns(good, 4)
        if len(bad) > 0:
            print(f"{len(bad)}/{len(tested)} keywords have a value not in the allowed list: ")
            for k in bad:
                print(f"{k} has value {mirisim_kwds[k]}")
                print(f"but must be one of")
                print(' '.join(str(i) for i in enum_kwds.loc[k, 'enum']))

    def test_all_headers_kwds_enum(self):
        for k in self.active_headers.keys():
            print(f"Testing {k}")
            self.test_kwd_enum_values(k)
            print("\n")

    def test_kwd_type(self, hdu_name):
        # first, get rid of all the enum, list-like values
        ref_kwds = self.get_ref_kwds_for_header(hdu_name)
        ref_kwds = ref_kwds[ref_kwds.isna()]

        # group by type
        gb_type = ref_kwds.groupby('type')

    def test_all_headers(self, func):
        for k in self.active_headers.keys():
            print(f"Testing {k}")
            func(k)
            print("\n")
