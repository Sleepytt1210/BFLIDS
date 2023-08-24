from typing import Tuple
import numpy as np
import pandas as pd
import os.path as path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


def csvfile(root_dir, train):
    # UNSW_NB15_testing-set.csv is actually more suitable for training because it has more data
    return path.join(root_dir, "UNSW_NB15_" + ("testing" if train else "training") + "-set.csv")


def load_data(path: str, num_clients: int, cid: int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load UNSW-NB15 (training and test set)."""
    print("Loading training set from", path)
    train_set = pd.read_csv(csvfile(path, True))
    print("Done loading training set")
    print("Loading testing set from", path)
    test_set = pd.read_csv(csvfile(path, False))

    # Combine the train and test set into one
    df = pd.concat([train_set, test_set])
    df = preprocess(df)

    # Partition data based on client id (Assume 5 clients => cid [0 ... 4])
    return partition(num_clients=num_clients, cid=cid, df=df)


def get_part(num_clients: int, cid: int, df: pd.DataFrame | np.ndarray):
    n = len(df)
    offset = int(n * 0.25)  # Data will have a 25% offset from start and
    start = (cid - 1) * offset
    end = n - (offset * int(num_clients - cid))
    return df[start:, :] if cid == num_clients else df[start:end, :]


def partition(num_clients: int, cid: int, df: pd.DataFrame):
    part = get_part(num_clients, cid, df)
    y = part[:, -1]
    X = part[:, :-1]
    return train_test_split(X, y, random_state=42, test_size=0.3, stratify=y)

# Select numeric categories


def rm_outliers(df_in: pd.DataFrame):
    result = df_in.copy()
    df_numeric = df_in.select_dtypes(include=[np.number])
    df_numeric.describe(include='all')

    # Remove outliers
    for feature in df_numeric.columns:
        if df_numeric[feature].max() > 10*df_numeric[feature].median() and df_numeric[feature].max() > 10:
            result[feature] = np.where(df_in[feature] < df_in[feature].quantile(
                0.95), df_in[feature], df_in[feature].quantile(0.95))
    return result


# Reduce labels of categorical features
def reduce_labels(df_in: pd.DataFrame):
    df_cat = df_in.select_dtypes(exclude=[np.number])
    for feature in df_cat.columns:
        if df_cat[feature].nunique() > 6:
            df_in[feature] = np.where(df_in[feature].isin(
                df_in[feature].value_counts().head().index), df_in[feature], '-')
    return df_in


# One hot encoding
def onehot(df_in: pd.DataFrame):
    ct = ColumnTransformer(
        [('onehot', OneHotEncoder(), [1, 2, 3])], remainder='passthrough')
    return np.array(ct.fit_transform(df_in))

# Normalise
# Function to min-max normalize


def normalize(df_in: pd.DataFrame, cols):
    """
    @param df pandas DataFrame
    @param cols a list of columns to encode
    @return a DataFrame with normalized specified features
    """
    result = df_in.copy()  # do not touch the original df
    for feature_name in cols:
        max_value = df_in[feature_name].astype('float').max()
        min_value = df_in[feature_name].astype('float').min()
        if max_value > min_value:
            result[feature_name] = (df_in[feature_name].astype(
                'float') - min_value) / (max_value - min_value)
    return result


def preprocess(df_in: pd.DataFrame):
    df_in = rm_outliers(df_in)
    df_in = reduce_labels(df_in)
    df_in = normalize(df_in, df_in.select_dtypes(include=[np.number]).columns)
    return onehot(df_in)
