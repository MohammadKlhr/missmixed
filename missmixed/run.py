import argparse
import os

import pandas as pd

from missmixed import MissMixed, Sequential, CategoricalListMaker


def main():
    parser = argparse.ArgumentParser(
        description="An easy-to-use command-line tool for Default MissMixed & MissMixed Trials. "
                    "for more info, check out our Github page: 'https://github.com/MohammadKlhr/missmixed'.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--path', '-p',
        type=str,
        required=True,
        help='Path to the input data file (e.g., CSV, XLSX).'
    )

    parser.add_argument(
        '--categorical-columns', '-cat-col',
        type=str,
        nargs='+',
        help=(
            'Names of categorical columns (space-separated). '
            'Use only one of: --categorical-columns, --categorical-index, '
            '--continuous-columns, or --continuous-index. '
            'If none are provided, all columns are treated as continuous (default).'
        )
    )

    parser.add_argument(
        '--categorical-index', '-cat-idx',
        type=int,
        nargs='+',
        help=(
            'Indices of categorical columns (space-separated). '
            'Use only one of: --categorical-columns, --categorical-index, '
            '--continuous-columns, or --continuous-index. '
            'If none are provided, all columns are treated as continuous (default).'
        )
    )

    parser.add_argument(
        '--continuous-columns', '-con-col',
        type=str,
        nargs='+',
        help=(
            'Names of continuous (non-categorical) columns (space-separated). '
            'Use only one of: --categorical-columns, --categorical-index, '
            '--continuous-columns, or --continuous-index. '
            'If none are provided, all columns are treated as continuous (default).'
        )
    )

    parser.add_argument(
        '--continuous-index', '-con-idx',
        type=int,
        nargs='+',
        help=(
            'Indices of continuous (non-categorical) columns (space-separated). '
            'Use only one of: --categorical-columns, --categorical-index, '
            '--continuous-columns, or --continuous-index. '
            'If none are provided, all columns are treated as continuous (default).'
        )
    )

    parser.add_argument(
        '--initial-strategy', '-s',
        type=str,
        default='mean',
        choices=['mean', 'median', 'most_frequent'],
        help='Initial strategy for filling NaN values.'
    )

    parser.add_argument(
        '--metric', '-m',
        type=str,
        default='r2_accuracy',
        choices=['r2_accuracy', 'mse'],
        help='Metric for model evaluation.'
    )

    parser.add_argument(
        '--trials', '-t',
        type=int,
        default=1,
        help='Trials numbers training imputers through all iterations.'
    )

    parser.add_argument(
        '--train-size', '-ts',
        type=float,
        default=0.9,
        help='Train size required for training imputers (val size, 1 - train size, is used for val/log).'
    )

    parser.add_argument(
        '--verbose', '-v',
        type=int,
        default=0,
        choices=[0, 1, 2],
        help='Verbosity level (0: silent, 1: default, 2: detailed).'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='imputed_data.csv',
        help='Path to save the output file. Defaults to "imputed_data.csv".'
    )

    args = parser.parse_args()

    input_path = args.path
    output_path = args.output
    categorical_cols = args.categorical_columns
    categorical_idx = args.categorical_index
    continuous_cols = args.continuous_columns
    continuous_idx = args.continuous_index
    initial_strategy = args.initial_strategy
    metric = args.metric
    trials = args.trials
    train_size = args.train_size
    verbose = args.verbose

    print(f"Input file path: {input_path}")
    print(f"Output file path: {output_path}")

    if categorical_cols is None and categorical_idx is None and continuous_cols is None and continuous_idx is None:
        print("Categorical columns: None")
        print("Non-categorical columns: All Columns")
    elif categorical_cols is not None:
        print(f"Categorical columns: {categorical_cols}")
    elif categorical_idx is not None:
        print(f"Categorical indices: {categorical_idx}")
    elif continuous_cols is not None:
        print(f"Non-categorical columns: {continuous_cols}")
    elif continuous_idx is not None:
        print(f"Non-categorical indices: {continuous_idx}")


    print(f"Initial fill strategy: {initial_strategy}")
    print(f"Evaluation metric: {metric}")
    print(f"Trials: {trials}")
    print(f"Train Size: {train_size}")
    print(f"Verbose level: {verbose}")

    if not os.path.exists(input_path):
        print(f"Error: The file at path '{input_path}' does not exist.")
        return

    try:
        # Load the data
        if input_path.endswith('.csv'):
            data = pd.read_csv(input_path)
        elif input_path.endswith('.xlsx'):
            data = pd.read_excel(input_path)
        else:
            print("Unsupported file format. Please use .csv or .xlsx.")
            return

        categorical_list_maker = CategoricalListMaker(data)

        if categorical_cols:
            categorical_columns = categorical_list_maker.make_categorical_list(categorical_columns=categorical_cols)
        elif categorical_idx:
            categorical_columns = categorical_list_maker.make_categorical_list(categorical_index=categorical_idx)
        elif continuous_cols:
            categorical_columns = categorical_list_maker.make_categorical_list(non_categorical_columns=continuous_cols)
        elif continuous_idx:
            categorical_columns = categorical_list_maker.make_categorical_list(non_categorical_index=continuous_idx)
        else:
            categorical_columns = categorical_list_maker.make_categorical_list()

        base_model = Sequential(trials=trials)

        # Perform imputation
        miss_mixed = MissMixed(data, initial_strategy=initial_strategy, sequential=base_model, metric=metric,
                               categorical_columns=categorical_columns, train_size=train_size, verbose=verbose)
        miss_mixed.fit_transform()
        result = miss_mixed.result()

        imputed_data = result['imputed_data']
        imputed_data.columns = data.columns

        # Save the imputed data to the specified output path
        imputed_data.to_csv(output_path, index=False)
        print(f"Data successfully imputed. Results saved to: {output_path}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
