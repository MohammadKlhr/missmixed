import argparse
import os
import sys

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
    '--column', '-col',
    type=str,
    nargs='+',
    help=(
        "Specify categorical or non-categorical columns by *name*.\n"
        "Format: <type> <col1> <col2> ...\n"
        "  <type> must be one of:\n"
        "    'cat' or 'categorical'        → treat listed columns as discrete (categorical)\n"
        "    'non-cat' or 'non-categorical' → treat listed columns as continuous (non-categorical)\n"
        "If no columns are listed after <type>, all columns are treated according to <type>.\n"
        "Examples:\n"
        "  --column cat age city       → 'age' and 'city' are categorical\n"
        "  --column non-cat income     → all except 'income' are categorical\n"
        "Note: Use only one of --column or --index. "
        "If neither is provided, all columns are treated as continuous (default)."
        )
    )

    parser.add_argument(
        '--index', '-idx',
        type=str,
        nargs='+',
        help=(
            "Specify categorical or non-categorical columns by *index* (0-based).\n"
            "Format: <type> <idx1> <idx2> ...\n"
            "  <type> must be one of:\n"
            "    'cat' or 'categorical'        → treat listed indices as discrete (categorical)\n"
            "    'non-cat' or 'non-categorical' → treat listed indices as continuous (non-categorical)\n"
            "If no indices are listed after <type>, all columns are treated according to <type>.\n"
            "Examples:\n"
            "  --index cat 0 2 4        → columns at indices 0, 2, 4 are categorical\n"
            "  --index non-cat 1 3      → all except indices 1, 3 are categorical\n"
            "Note: Use only one of --column or --index. "
            "If neither is provided, all columns are treated as continuous (default)."
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

    initial_strategy = args.initial_strategy
    metric = args.metric
    trials = args.trials
    train_size = args.train_size
    verbose = args.verbose
    
    index = args.index
    column = args.column
    
    categorical_idx = None
    continuous_idx=None
    categorical_cols = None
    continuous_cols=None
    
    if index is not None:
        t = index[0]
        if t == 'cat' or t == 'categorical':
            if len(index) > 1:
                categorical_idx = [int(i) for i in index[1:]]
            else:
                continuous_idx = []
        elif t == 'non-cat' or t == 'non-categorical':
            if len(index) > 1:
                continuous_idx = [int(i) for i in index[1:]]
            else:
                categorical_idx = []
        else:
            print("\033[31mInvalid type specified for --index.\033[0m")
            print("Valid options are: 'cat', 'categorical', 'non-cat', 'non-categorical'.")
            print("Example usage:")
            print("  --index cat 0 2 4        (treat columns 0, 2, 4 as categorical)")
            print("  --index non-cat 1 3      (treat all except 1, 3 as categorical)")
            print("\033[33mProceeding with default: all columns treated as continuous.\033[0m")

            
    elif column is not None:
        t = column[0]
        if t == 'cat' or t == 'categorical':
            if len(column) > 1:
                categorical_cols = column[1:]
            else:
                continuous_cols = []
        elif t == 'non-cat' or t == 'non-categorical':
            if len(column) > 1:
                continuous_cols = column[1:]
            else:
                categorical_cols = []
        else:
            print("\033[31mInvalid type specified for --column.\033[0m")
            print("Valid options are: 'cat', 'categorical', 'non-cat', 'non-categorical'.")
            print("Example usage:")
            print("  --column cat age city    (treat 'age' and 'city' as categorical")
            print("  --column non-cat income  (treat all except 'income' as categorical)")
            print("\033[33mProceeding with default: all columns treated as continuous.\033[0m")


    print(f"Input file path: {input_path}")
    print(f"Output file path: {output_path}")

    print(f"Initial fill strategy: {initial_strategy}")
    print(f"Evaluation metric: {metric}")
    print(f"Trials: {trials}")
    print(f"Train Size: {train_size}")
    print(f"Verbose level: {verbose}")

    if not os.path.exists(input_path):
        print(f"\033[31mError: The file at path '{input_path}' does not exist.\033[0m")
        return

    try:
        # Load the data
        if input_path.endswith('.csv'):
            data = pd.read_csv(input_path)
        elif input_path.endswith('.xlsx'):
            data = pd.read_excel(input_path)
        else:
            print("\033[31mError: Unsupported input file format. Please use .csv or .xlsx.\033[0m")
            return
        
        if output_path.endswith('.csv') == False and output_path.endswith('.xlsx') == False:
            print("\033[31mError: Unsupported output file format. Please use .csv or .xlsx.\033[0m")
            return

        categorical_list_maker = CategoricalListMaker(data)

        if categorical_cols is not None:
            categorical_columns = categorical_list_maker.make_categorical_list(categorical_columns=categorical_cols)
            print(f"Categorical columns: {categorical_cols}")
        elif categorical_idx is not None:
            categorical_columns = categorical_list_maker.make_categorical_list(categorical_index=categorical_idx)
            print(f"Categorical indices: {categorical_idx}")
        elif continuous_cols is not None:
            categorical_columns = categorical_list_maker.make_categorical_list(non_categorical_columns=continuous_cols)
            print(f"Non-categorical columns: {continuous_cols}")
        elif continuous_idx is not None:
            categorical_columns = categorical_list_maker.make_categorical_list(non_categorical_index=continuous_idx)
            print(f"Non-categorical indices: {continuous_idx}")
        else:
            categorical_columns = categorical_list_maker.make_categorical_list()
            print(f"Non-categorical columns: All Columns")

        base_model = Sequential(trials=trials)

        # Perform imputation
        miss_mixed = MissMixed(data, initial_strategy=initial_strategy, sequential=base_model, metric=metric,
                               categorical_columns=categorical_columns, train_size=train_size, verbose=verbose)
        miss_mixed.fit_transform()
        result = miss_mixed.result()

        imputed_data = result['imputed_data']
        imputed_data.columns = data.columns

        # Save the imputed data to the specified output path
        if output_path.endswith('.csv'):
            imputed_data.to_csv(output_path, index=False)
        elif output_path.endswith('.xlsx'):
            imputed_data.to_excel(output_path, index=False)
        print(f"\033[32mData successfully imputed. Results saved to: {output_path}\033[0m")

    except Exception as e:
        print(f"\033[31mAn unexpected error occurred: {e}\033[0m")
        
if __name__ == "__main__":
    main()
