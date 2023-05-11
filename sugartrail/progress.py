import sugartrail
import IPython

class Progress:
    """Class attributes store the progress of each hop."""
    def __init__(self):
        self.pre_print = ""
        self.intro_print = ""
        self.processed_officers  = []
        self.processed_companies = []
        self.processed_addresses = []
        self.address_index = 0
        self.officer_index = 0
        self.company_index = 0
        self.selected_addresses = []
        self.selected_companies = []
        self.selected_officers = []
        self.outro_print = ""

    def print_progress(self):
        IPython.display.clear_output(wait=True)
        if self.pre_print:
            print(self.pre_print)
            print("-------------")
        if self.intro_print:
            print(self.intro_print)
        if self.processed_addresses:
            print("Processed " + str(self.address_index+1) + "/" + str(len(self.selected_addresses)) + " addresses.")
        if self.processed_companies:
            print("Processed " + str(self.company_index+1) + "/" + str(len(self.selected_companies)) + " companies.")
        if self.processed_officers:
            print("Processed " + str(self.officer_index+1) + "/" + str(len(self.selected_officers)) + " officers.")
        if self.outro_print:
            print(self.outro_print)
