import pandas as pd

class PandasHelpers:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def load_csv(self, file_path):
        """ Loads a CSV file into the DataFrame. """
        self.dataframe = pd.read_csv(file_path)

    def save_csv(self, file_path):
        """ Saves the DataFrame to a CSV file. """
        self.dataframe.to_csv(file_path, index=False)

    def filter_by_condition(self, column, condition):
        """ Filters the DataFrame based on a condition in a specific column. """
        return self.dataframe[self.dataframe[column] == condition]

    def calculate_summary_statistics(self):
        """ Returns summary statistics for the DataFrame. """
        return self.dataframe.describe()

    def merge_with(self, other_df, key, how='inner'):
        """ Merges the current DataFrame with another DataFrame on a specified key. """
        self.dataframe = pd.merge(self.dataframe, other_df, on=key, how=how)

    def drop_duplicates(self, column):
        """ Drops duplicate rows based on a specific column. """
        self.dataframe = self.dataframe.drop_duplicates(subset=[column])

    def add_column(self, column_name, data):
        """ Adds a new column to the DataFrame. """
        if len(data) == len(self.dataframe):
            self.dataframe[column_name] = data
        else:
            raise ValueError("Length of data does not match number of rows in DataFrame")

    def remove_column(self, column_name):
        """ Removes a column from the DataFrame. """
        self.dataframe.drop(column_name, axis=1, inplace=True)
