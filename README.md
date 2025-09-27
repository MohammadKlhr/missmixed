# MissMixed

## A Configurable Framework for Iterative Missing Data Imputation

**MissMixed** is a Python library designed for flexible and modular imputation of missing values in tabular datasets. It supports a wide range of imputation strategies, including ensemble methods, trial-based model selection, and deep learning integration — all within a customizable iterative architecture.

## 🔍 What is MissMixed?

MissMixed is not just a single algorithm — it’s a **framework** for building **iteration-wise, model-aware imputation pipelines**. It enables users to:

- Handle continuous, categorical, or mixed-type features
- Define custom model configurations at each iteration
- Combine multiple imputation algorithms (e.g., RandomForest, KNN, Deep Neural Networks)
- Dynamically evaluate and update imputed values using internal validation

Whether you’re working with low-dimensional medical data or large-scale mixed-type datasets, MissMixed is designed to offer **accuracy**, **adaptability**, and **interpretability**.

## 🚀 Installation

```bash
pip install missmixed
```

### 📦 Requirements

- Python ≥ 3.10
- NumPy
- Pandas
- scikit-learn
- XGBoost
- TensorFlow or Keras (for deep model imputation)
- tqdm

Dependencies will be installed automatically via pip.

### 📖 Usage

See the [example](./examples) folder for how to define:
Custom Iteration Architectures
Mixed-type pipelines
Trial-based imputation workflows

OR

Use Command-Line Interface (CLI)

```bash
 missmixed --path .\input_data.csv
```

#### 💻 MissMixed CLI Options

The following table lists **all command-line arguments** for MissMixed:

| Argument             | Short  | Type         | Default            | Description                                                                                                                                                                                                                                                                                                                                                                                                                              |
| -------------------- | ------ | ------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--path`             | `-p`   | `str`        | **required**       | Path to the input data file (CSV or XLSX).                                                                                                                                                                                                                                                                                                                                                                                               |
| `--column`           | `-col` | `str (list)` | `None`             | Specify categorical or non-categorical columns **by name**. Format: `<type> <col1> <col2> ...`<br>• `<type>` must be `cat` / `categorical` or `non-cat` / `non-categorical`.<br>• If no columns are listed after `<type>`, all columns are treated according to `<type>`.<br>Example:<br>`--column cat age city` → treat `age` and `city` as categorical.<br>`--column non-cat income` → treat all except `income` as categorical.       |
| `--index`            | `-idx` | `int (list)` | `None`             | Specify categorical or non-categorical columns **by index** (0-based). Format: `<type> <idx1> <idx2> ...`<br>• `<type>` must be `cat` / `categorical` or `non-cat` / `non-categorical`.<br>• If no indices are listed after `<type>`, all columns are treated according to `<type>`.<br>Example:<br>`--index cat 0 2 4` → treat columns 0, 2, 4 as categorical.<br>`--index non-cat 1 3` → treat all except columns 1, 3 as categorical. |
| `--initial-strategy` | `-s`   | `str`        | `mean`             | Initial strategy for filling NaN values. Choices: `mean`, `median`, `most_frequent`.                                                                                                                                                                                                                                                                                                                                                     |
| `--metric`           | `-m`   | `str`        | `r2_accuracy`      | Metric for model evaluation. Choices: `r2_accuracy`, `mse`.                                                                                                                                                                                                                                                                                                                                                                              |
| `--trials`           | `-t`   | `int`        | `1`                | Number of trials for training imputers through all iterations.                                                                                                                                                                                                                                                                                                                                                                           |
| `--train-size`       | `-ts`  | `float`      | `0.9`              | Train size ratio (validation size = `1 - train_size`).                                                                                                                                                                                                                                                                                                                                                                                   |
| `--verbose`          | `-v`   | `int`        | `0`                | Verbosity level: `0` (silent), `1` (default), `2` (detailed).                                                                                                                                                                                                                                                                                                                                                                            |
| `--output`           | `-o`   | `str`        | `imputed_data.csv` | Path to save the imputed output file. Supports `.csv` or `.xlsx`.                                                                                                                                                                                                                                                                                                                                                                        |


## 📄 License

MIT License

### 📣 Citation

[1] M. M. Kalhori, M. Izadi, “A Novel Mixed-Method Approach to Missing Value Imputation: An Introduction to MissMixed”, 29th International Computer Conference, Computer Society of Iran (CSICC) – IEEE, 2025.

[2] M. M. Kalhori, M. Izadi, F. Akbari “MissMixed: An Adaptive, Extensible and Configurable Multi-Layer Framework for Iterative Missing Value Imputation”, IEEE Access, 2025 (under review).
