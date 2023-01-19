# Sugartrail

![title](assets/images/candystreet.png)

Sugartrail is a network analysis and visualisation tool developed to make it easier and faster for researchers to explore connections between companies, officers and addresses within Companies House.

## Requirements

You will require an API key from Companies House to get data. First you will need to create a live application to get an API key which you can do by following the [Companies House guide](https://developer.company-information.service.gov.uk/how-to-create-an-application).

## No-Install Usage

A hosted demo of the Sugartrail dashboard can be accessed [here](https://stark-island-99644.herokuapp.com/) (might take a few seconds to load the page).

## Demo

[![img](assets/images/demo.png)](https://www.youtube.com/watch?v=evPXGTj33LQ)

## Installation

1. Make sure you have Conda installed

2. Download the tool's repository using the command:

```bash
git clone https://github.com/ribenamaplesyrup/sugartrail.git
```

3. Navigate to the main directory and run:

```bash
conda env create -f config/environment.yml
conda activate candystore
pip install -e .
jupyter nbextension enable --py --sys-prefix ipyleaflet
```

4. For a quickstart run `voila --no-browser --debug --Voila.ip=0.0.0.0 dashboard/Sugartrail.ipynb --VoilaConfiguration.file_whitelist="['.*']"` and navigate to the url printed in your terminal where Voilà is running at (no-code). For a more detailed explanation of the tool's capabilities, run `jupyter notebook notebooks` and open either `quickstart.ipynb` or `001_getting_started.ipynb`.
