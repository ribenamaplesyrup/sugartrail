# Sugartrail

## Tool Description

Sugartrail is a work-in-progress network analysis tool and workflow that helps researchers to use a suspicious company director to discover other suspicious companies, directors and locations through Companies House.

The workflow is based on the following observations:

- suspicious directors often have many active appointments registered to multiple historic addresses
- addresses with many registered businesses can contain multiple scam businesses

## Requirements

You will require an API key from Companies House to authenticate with the API. First you will need to create a live application to get an API key which you can do by following the [Companies House guide](https://developer.company-information.service.gov.uk/how-to-create-an-application). You will then need to manually hard-code the API key inside the `sugartrail.py` script as the value for `access_token`.

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
jupyter notebook
```
4. Open `Tutorial 1 - Exit Through the Candy Shop`

## Usage

- A walkthrough of how to use the tool is included in the linked Jupyter notebook showing how we can get from suspicious Candy Stores of Oxford Street to several prolific scammers.
