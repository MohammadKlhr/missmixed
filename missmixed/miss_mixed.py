import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from typing import List, Tuple, Literal, Dict, Any
from missmixed.utils import train_test_split, SharedData
from missmixed.architecture import Sequential
from sklearn.metrics import r2_score, accuracy_score, mean_squared_error
from tqdm import tqdm
from sklearn.preprocessing import LabelEncoder

acceptable_metrics = ['r2_accuracy', 'mse']

ITERATION_BAR_FORMAT = "{l_bar}{bar}| Iteration {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"

"""
MissMixed: A class for handling missing data imputation in mixed-type datasets (categorical and numerical).

This class provides functionality to impute missing values in datasets containing both categorical and numerical
columns. It uses a sequence of imputation models (defined in the `Sequential` class) to iteratively impute missing
values and evaluate the performance of the imputation process.

Attributes:
    raw_data (pd.DataFrame): The original dataset with missing values.
    working_data (pd.DataFrame): A copy of the original dataset used for processing.
    sequential (Sequential): An instance of the `Sequential` class containing a sequence of imputers.
    categorical_columns (List[bool]): A list indicating whether each column is categorical (True) or numerical (False).
    train_size (float): The proportion of the dataset to use for training (default: 0.9).
    verbose (Literal[0, 1, 2]): Verbosity level for logging (0: silent, 1: minimal, 2: detailed).
    early_stopping (bool): Whether to enable early stopping based on the number of updated columns.
    iter_per_stopping (int): Number of iterations to consider for early stopping.
    tolerance_percentage (float): Tolerance percentage for early stopping.
    shared (SharedData): An instance of `SharedData` for sharing information across methods.
    num_of_columns (int): The number of columns in the dataset.
    imputed_df (pd.DataFrame): A DataFrame to store the imputed values.
    metric_direction (int): Indicates whether the metric should be maximized (1) or minimized (-1).
    non_categorical_metric (callable): Metric function for numerical columns (e.g., R2 score or MSE).
    categorical_metric (callable): Metric function for categorical columns (e.g., accuracy or MSE).
    max_metric_tests (np.ndarray): Array to store the best metric scores for each column.

Methods:
    __init__: Initializes the MissMixed class with the dataset, imputation models, and configuration.
    __clean_working_data: Drops columns with all NaN values from the dataset.
    __process_categorical_data: Encodes categorical columns using LabelEncoder.
    __init_metrics: Initializes the metric functions based on the specified metric.
    fit_transform: Performs the imputation process iteratively using the sequence of imputers.
    __process_each_imputer: Processes each imputer in the sequence and updates the imputed values.
    process_each_column: Trains and evaluates the imputation model for a specific column.
    can_impute: Checks if the imputation for a column should be performed based on the metric score.
    __apply_best_model: Applies the best model to impute missing values in a column.
    __set_metric: Sets the appropriate metric function based on the column type.
    __iteration_progress_bar: Returns a progress bar for the imputation iterations.
    __check_early_stopping: Checks if early stopping conditions are met.
    __dataset_preparation: Prepares the dataset for training and imputation.
    result: Returns the imputed dataset and the best metric scores.
    _log: Logs messages based on the verbosity level.
    normalize: Normalizes numerical columns in the dataset.
"""


class MissMixed:
    def __init__(self,
                 raw_data: pd.DataFrame,
                 sequential: Sequential,
                 categorical_columns: List[bool],
                 metric: Literal['r2_accuracy', 'mse'] = 'r2_accuracy',
                 initial_strategy: Literal['mean', 'median', 'most_frequent', 'constant'] = 'mean',
                 train_size: float = 0.9,
                 early_stopping: bool = False,
                 iter_per_stopping: int = 1,
                 tolerance_percentage: float = 0.1,
                 verbose: Literal[0, 1, 2] = 0
                 ):
        """
        Initializes the MissMixed class.

        Args:
            raw_data (pd.DataFrame): The dataset with missing values.
            sequential (Sequential): An instance of the `Sequential` class containing a sequence of imputers.
            categorical_columns (List[bool]): A list indicating whether each column is categorical (True) or numerical (False).
            metric (Literal['r2_accuracy', 'mse']): The metric to use for evaluating imputation performance (default: 'r2_accuracy').
            initial_strategy (Literal['mean', 'median', 'most_frequent', 'constant']): The strategy for initial imputation (default: 'mean').
            train_size (float): The proportion of the dataset to use for training (default: 0.9).
            early_stopping (bool): Whether to enable early stopping (default: False).
            iter_per_stopping (int): Number of iterations to consider for early stopping (default: 1).
            tolerance_percentage (float): Tolerance percentage for early stopping (default: 0.1).
            verbose (Literal[0, 1, 2]): Verbosity level for logging (default: 0).
        """
        self.raw_data = raw_data.copy()
        self.working_data = raw_data.copy()
        self.sequential = sequential
        self.categorical_columns = categorical_columns
        self.train_size = train_size
        self.verbose = verbose
        self.early_stopping = early_stopping
        self.iter_per_stopping = iter_per_stopping
        self.tolerance_percentage = tolerance_percentage
        self.shared = SharedData()
        self.__clean_working_data()
        self.__process_categorical_data()
        self.num_of_columns = self.working_data.shape[1]
        self.imputed_df = pd.DataFrame(SimpleImputer(strategy=initial_strategy).fit_transform(self.working_data))
        self.__init_metrics(metric)

    def __clean_working_data(self):
        """
        Drops columns with all NaN values from the dataset.
        """
        non_null_count_per_column = self.working_data.notna().sum()
        columns_to_be_dropped = non_null_count_per_column[non_null_count_per_column <= 1].index
        for i in columns_to_be_dropped:
            del self.categorical_columns[i]
        if columns_to_be_dropped.size >= 1:
            self._log(0, f'Columns with all NaN values {columns_to_be_dropped} are dropped')
        self.working_data.drop(columns=columns_to_be_dropped, inplace=True)

    def __process_categorical_data(self):
        """
        Encodes categorical columns using LabelEncoder.
        """
        self.column_to_encoder = {}
        # keep number of categories per column
        category_counts = [1] * self.working_data.shape[1]

        for col_idx, is_categorical in enumerate(self.categorical_columns):
            if is_categorical:
                encoder = LabelEncoder()
                # count unique values in column
                col = self.working_data.iloc[:, col_idx]
                non_null_mask = col.notna()
                self.working_data.iloc[:, col_idx][non_null_mask] = encoder.fit_transform(col[non_null_mask])
                self.column_to_encoder[col_idx] = encoder
                category_counts[col_idx] = len(encoder.classes_)

        self.shared.set_value('categorical_columns', self.categorical_columns)
        self.shared.set_value('category_counts', category_counts)

    def __init_metrics(self, metric):
        """
        Initializes the metric functions based on the specified metric.

        Args:
            metric (Literal['r2_accuracy', 'mse']): The metric to use for evaluating imputation performance.
        """
        if metric not in acceptable_metrics:
            raise ValueError(f'Invalid metric {metric}. Only {acceptable_metrics} are acceptable.')
        self.metric_direction = 1 if metric == 'r2_accuracy' else -1
        self.non_categorical_metric = r2_score if metric == 'r2_accuracy' else mean_squared_error
        self.categorical_metric = accuracy_score if metric == 'r2_accuracy' else mean_squared_error

        self.max_metric_tests = np.full(self.num_of_columns, -np.inf * self.metric_direction)

    def fit_transform(self):
        """
        Performs the imputation process iteratively using the sequence of imputers.
        """
        # keep number of columns that updated per iteration
        updated_columns_count = []
        for idx, imputer in enumerate(self.__iteration_progress_bar()):
            self._log(1, f'Iteration {idx + 1}/{len(self.sequential.imputers)}')
            count = self.__process_each_imputer(imputer)

            self._log(1, f'---- {count} columns updated ----')
            self._log(1, '--' * 40)
            updated_columns_count.append(count)

            if self.__check_early_stopping(updated_columns_count):
                print('Early stopping condition hits!')

    def __process_each_imputer(self, imputer) -> int:
        """
        Processes each imputer in the sequence and updates the imputed values.

        Args:
            imputer: The imputer to process.

        Returns:
            int: The number of columns updated in this iteration.
        """
        updated_column_count = 0
        columns_scores_history = {'train': [], 'val': []}
        for col_idx in range(self.num_of_columns):
            self.shared.set_value('processing_col_idx', col_idx)
            # todo need to refactor
            is_categorical = self.categorical_columns[col_idx]
            self.shared.set_value('is_categorical', self.categorical_columns[col_idx])
            self.__set_metric()
            imputer.set_model(is_categorical)

            if imputer.model is None:
                self._log(2, f'Imputer skipped because not found proper imputer model')
                continue
            self._log(2, f"Imputing column {col_idx + 1}/{self.num_of_columns}")

            if not self.raw_data.iloc[:, col_idx].isnull().any():
                self._log(2, f'Imputation skipped, there is no null value')
                self.__can_impute(col_idx, 1 if self.metric_direction else 0)
                continue

            is_column_updated, column_score = self.__process_each_column(imputer, col_idx)

            if is_column_updated:
                updated_column_count += 1
            columns_scores_history['train'].append(column_score['train'])
            columns_scores_history['val'].append(column_score['val'])
        # self._log(1, f'{updated_column_count} columns updated')
        self._log(1,
                  f'Average {self.metric.__name__} train: {np.mean(columns_scores_history["train"])}, validation: {np.mean(columns_scores_history["val"])}')

        return updated_column_count

    def __process_each_column(self, imputer, col_index: int) -> tuple[bool, dict[str, list[Any]]]:
        """
        Trains and evaluates the imputation model for a specific column.

        Args:
            imputer: The imputer to use.
            col_index (int): The index of the column to process.

        Returns:
            tuple[bool, dict[str, list[Any]]]: A tuple containing a boolean indicating if the column was updated
                                               and a dictionary of metric scores for training and testing.
        """
        is_column_updated = False
        column_score = {'train': [], 'val': []}
        ds, impute_ds = self.__dataset_preparation(col_index)
        if len(ds['y_test']) >= 2:
            metric_scores, models = [], []
            # Train model and select best model based score on test data
            for _ in range(imputer.trials):
                imputer.fit(ds['x_train'], ds['y_train'])
                y_pred_train = np.maximum(imputer.predict(ds['x_train']), 0.0)
                y_pred_test = np.maximum(imputer.predict(ds['x_test']), 0.0)
                metric_scores.append(
                    {
                        'train': self.metric(ds['y_train'], y_pred_train),
                        'val': self.metric(ds['y_test'], y_pred_test)
                    }
                )
                models.append(imputer.copy())

            best_index = np.argmax([m['val'] * self.metric_direction for m in metric_scores])
            best_metric_score = metric_scores[best_index]
            column_score['train'].append(best_metric_score['train'])
            column_score['val'].append(best_metric_score['val'])

            self._log(2, f"Best {self.metric.__name__} results: {best_metric_score}")
            if self.__can_impute(col_index, best_metric_score['val']):
                self.__apply_best_model(models[best_index], impute_ds, col_index)
                is_column_updated = True
                self._log(2, '-- Column updated --')

        return is_column_updated, column_score

    def __can_impute(self, col_index: int, test_score: float) -> bool:
        """
        Checks if the imputation for a column should be performed based on the metric score.

        Args:
            col_index (int): The index of the column.
            test_score (float): The metric score for the column.

        Returns:
            bool: True if the imputation should be performed, False otherwise.
        """
        do = self.max_metric_tests[col_index] * self.metric_direction < test_score * self.metric_direction
        if do:
            self.max_metric_tests[col_index] = test_score

        return do

    def __apply_best_model(self, model, impute_dataset, col_index: int):
        """
        Applies the best model to impute missing values in a column.

        Args:
            model: The best model to use for imputation.
            impute_dataset (dict): The dataset containing missing values.
            col_index (int): The index of the column to impute.
        """
        y_pred_to_impute = model.predict(impute_dataset['x'])
        self.imputed_df.loc[impute_dataset['y'].index, col_index] = y_pred_to_impute

    def __set_metric(self):
        """
        Sets the appropriate metric function based on the column type.
        """
        self.metric = self.categorical_metric if self.shared.get_value(
            'is_categorical') else self.non_categorical_metric

    def __iteration_progress_bar(self):
        """
        Returns a progress bar for the imputation iterations.

        Returns:
            tqdm or list: A progress bar or the list of imputers, depending on the verbosity level.
        """
        if self.verbose == 0:
            iteration_progress_bar = tqdm(
                self.sequential.imputers,
                desc="Imputing...: ",
                bar_format=(
                    ITERATION_BAR_FORMAT
                ))
        else:
            iteration_progress_bar = self.sequential.imputers
        return iteration_progress_bar

    def __check_early_stopping(self, updated_columns_count: List[int]) -> bool:
        """
        Checks if early stopping conditions are met.

        Args:
            updated_columns_count (List[int]): A list of the number of columns updated in each iteration.

        Returns:
            bool: True if early stopping conditions are met, False otherwise.
        """
        if self.early_stopping:
            if len(updated_columns_count) >= self.iter_per_stopping:
                for updated_columns in updated_columns_count[-1 * self.iter_per_stopping:]:
                    if updated_columns / self.num_of_columns > self.tolerance_percentage:
                        return False
                return True
        return False

    def __dataset_preparation(self, col_index: int):
        """
        Prepares the dataset for training and imputation.

        Args:
            col_index (int): The index of the column to prepare the dataset for.

        Returns:
            tuple[dict, dict]: A tuple containing the training dataset and the imputation dataset.
        """
        features_df = self.imputed_df.drop(columns=[col_index])
        target_series = self.working_data.iloc[:, col_index]
        normalized_features = self.__normalize(features_df.columns, features_df)
        y_non_missing = target_series.dropna()
        x_non_missing = normalized_features.loc[y_non_missing.index]
        y_missing = target_series[target_series.isnull()]
        x_missing = normalized_features.loc[y_missing.index]
        x_train, y_train, x_test, y_test = train_test_split(x_non_missing, y_non_missing, train_size=self.train_size)

        train_dataset = {
            'x_train': x_train,
            'y_train': y_train,
            'x_test': x_test,
            'y_test': y_test
        }

        impute_dataset = {
            'x': x_missing,
            'y': y_missing
        }

        return train_dataset, impute_dataset

    def result(self):
        """
        Returns the imputed dataset and the best metric scores.

        Returns:
            dict: A dictionary containing the imputed dataset and the best metric scores.
        """
        for i in range(self.num_of_columns):
            if self.categorical_columns[i]:
                self.imputed_df.iloc[:, i] = self.column_to_encoder[i].inverse_transform(self.imputed_df.iloc[:, i].astype('int64'))

        return {
            'imputed_data': self.imputed_df,
            'scores': self.max_metric_tests
        }

    def _log(self, level, *message):
        """
        Logs messages based on the verbosity level.

        Args:
            level (int): The verbosity level (0, 1, or 2).
            *message: The message(s) to log.
        """
        if self.verbose >= level:
            print(" ".join(map(str, message)))

    def __normalize(self, col_names, df_x):
        """
        Normalizes numerical columns in the dataset.

        Args:
            col_names: The names of the columns to normalize.
            df_x (pd.DataFrame): The DataFrame containing the columns to normalize.

        Returns:
            pd.DataFrame: The normalized DataFrame.
        """
        cols_min = []
        cols_max = []
        for col_name in col_names:
            if not self.shared.is_categorical():
                col_min = df_x[col_name].min()
                col_max = df_x[col_name].max()
                cols_min.append(col_min)
                cols_max.append(col_max)
                df_x[col_name] = ((df_x[col_name] - col_min) / (col_max - col_min)) * 10

        return df_x
