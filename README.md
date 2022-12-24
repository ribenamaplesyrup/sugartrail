# Sugartrail

![title](assets/images/domain.png)

Sugartrail is a network analysis and visualisation tool developed to make it easier and faster for researchers to explore connections between companies, officers and addresses within Companies House.

## Requirements

You will require an API key from Companies House to get data. First you will need to create a live application to get an API key which you can do by following the [Companies House guide](https://developer.company-information.service.gov.uk/how-to-create-an-application).

## Installation

1. Make sure you have Conda installed

2. Download the tool's repository using the command:

```bash
git clone https://github.com/ribenamaplesyrup/sugartrail.git
```

3. Navigate to the main directory and run:

```bash
conda env create -f environment.yml
conda activate candystore
jupyter nbextension enable --py --sys-prefix ipyleaflet
jupyter notebook
```

## Usage

Navigate to `Quickstart.ipynb` to run the tool without needing to use the API. For a more detailed explanation of the tool's capabilities, head to `Tutorial 1 - Get Started`. 
