# Galaxy and Cosmology Spectroscopic Surveys Dashboard

This repository contains the code and survey data library for the Galaxy and Cosmology Spectroscopic Surveys Dashboard. The dashboard is a web-based tool that allows users to explore and filter the vast array of literature spectroscopic surveys. The dashboard is hosted at [specsurveysdb.onrender.com](https://specsurveysdb.onrender.com).

Significant acknowledgement goes to Ivan Baldry and his [long-running compilation of spectroscopic surveys](https://www.astro.ljmu.ac.uk/~ikb/research/galaxy-redshift-surveys.html), which was the starting point for this project.

Current functionality:
- Filter surveys by status and facility: Select the status of the survey (ongoing, completed, planned/proposed). In addition, select one or more specific facilities to filter the surveys by.
- Download data: Download the filtered survey data in CSV format. Note that the data is filtered based on the selected status and facilities, changes based on the selection wavelengh in the legend will not be reflected in the downloaded data (i.e. all selection wavelengths will be present).


## Adding New Surveys / Amending Existing Surveys

Information for each survey is defined in the corresponding '.json' file in the 'surveys' directory. To add a new survey, first fork the repository and then create a new '.json' file in the 'surveys' directory. The '.json' file should have the following structure:

```json
{
    "Survey": str # Short survey name / acronym,
    "Full Name": str # Full Name of Survey with relevant acronym expandeds,
    "Reference": str # DOI to the primary survey publication,
    "Nspec": int # Number of spectra in the survey,
    "Area": float # Survey area in square degrees,
    "Status": [0, 1, 2] # Survey status: 0 = Ongoing, 1 = Completed, 2 = Planned/Proposed,
    "Selection Type": [0, 1, 2] # Selection type: 0 = magnitude selection, 1 = colour selection, 2 = other,
    "Selection Wavelength": str # Selection wavelength: ['X-ray', 'UV', '300-500nm', '500-950nm', '0.95-2.5µm', '2.5-5µm', '5-1000µm', 'Radio'],
    "Facility": str # Telescope / Facility used for survey,
    "Instrument": str # Instrument used for survey, if applicable. 
                        If multiple instruments were used, list the primary instrument,
                         with others listed in the 'Notes' field.
    "Notes": str # Any additional notes on the survey, including additional instruments used,
                    survey status, selection criteria, etc.
}
```

Once the '.json' file has been created, submit a pull request to the main repository. The new survey will be added to the dashboard once the pull request has been reviewed and merged. Similarly, to amend an existing survey, edit the corresponding existing '.json' file and submit a pull request.

## Adding Additional Survey Properties

Additional survey properties can be added to the '.json' files, for example spectral resolution, redshift ranges. These can be added as additional key-value pairs in the '.json' file. They will automatically be included in the compiled survey data, however the dashboard will need to be updated to include these new properties in the display. Future updates to the dashboard may include the ability to filter surveys based on these additional properties. Particular requests for additional properties can be made by opening an issue on the repository.

## Running the Dashboard Locally

To run the dashboard locally, first clone the repository and then install the required packages using the following command:

```bash
pip install -r requirements.txt
```

Once the required packages have been installed, the app.py script may need amended to remove the 'host' and 'port' arguments in the 'app.run()' function. Once this is done, run the following command to start the dashboard:

```bash
python app.py
```

The dashboard will be accessible at `http://http://127.0.0.1` in your web browser.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.