#import pytest
import yaml
from pathlib import Path
import pandas as pd
from astropy.io import fits


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


    def get_ref_kwds_for_header(self, hdu_name):
        """For a header, pull out the keywords that should be in it"""
        ref_kwds = self.ref_kwds.query('fits_hdu == @hdu_name')['fits_keyword']
        return ref_kwds

    def test_kwds_exist(self, hdu_name):
        """
        Test a header to see which keywords do and do not exist
        """
        ref_kwds = self.get_ref_kwds_for_header(hdu_name)
        test_hdr = self.active_headers[hdu_name]
        kwds_exist = ref_kwds.apply(lambda x: x in test_hdr.keys())
        kwds_present = ref_kwds[kwds_exist[kwds_exist].index]
        kwds_missing = ref_kwds[kwds_exist[~kwds_exist].index]

        print(f"Testing {hdu_name}")
        print(f"{len(kwds_present)}/{len(kwds_exist)} expected keywords were found.")
        print("The following keywords *do* exist:")
        print("\t"+"\n\t".join(kwds_present))
        print("The following keywords *do not* exist:")
        print("\t"+"\n\t".join(kwds_missing))

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

    def test_all_headers_kwsd_exist(self):
        for k in self.active_headers.keys():
            print("\n")
            self.test_kwds_exist(k)
