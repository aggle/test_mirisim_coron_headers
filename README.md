# test_mirisim_coron_headers

`schema_folder` contains definitions for all the expected metadata keywords and values in the JWST data. They are available for inspection and/or download from the JWST keyword dictionary here: https://mast.stsci.edu/portal/Mashup/Clients/jwkeywords/. This module and notebook collects all the metadata that is expected to be in the MIRI coronagraphic mode data, and checks it against MIRISim output data. 

## Usage
At the top of `test_data-headers.ipynb`, replace `data_files` with a list of the files you want to test. Then run the notebook and look at the output!

## Tests
Right now the notebook works by printing out information for the user, and it is up to the user to decide if the information is correct or not.

### Tests for existence
This test is simply to see if an expected keyword is present or not in the MIRISim headers. It turns out that of the ~300 keywords that are listed in the JWST keyword dictionary as being included in MIRISim coronagraphy data, fewer than 100 of them are used by MIRISim.

For each header, the test function will print a list of expected keywords that *were* found, and a list of expected keywords that were *not* found.

### Tests for keywords that must have one value from an enumerated list
Some of the keywords must have one value out of a small set. For example, `CORONMSK` must take one of the following values: `LYOT, LYOT_2300, 4QPM, 4QPM_1065, 4QPM_1140, 4QPM_1550`. This test checks that each of these kinds of keywords is assigned one of its allowed values. It will print all the keywords that pass the test, and for all the keywords that fail the test, it will print both the bad value and the list of allowed values.

### Tests for type
This is a less specific test, which checks only that the *type* of the value assigned to a particular keyword matches what is specified in the JWST keyword dictionary. For the keywords that fail this test, it will print their name, specified type, and assigned value.
