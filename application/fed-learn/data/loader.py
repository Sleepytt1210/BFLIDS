from typing import Tuple
import numpy as np
import pandas as pd
import os.path as path
from sklearn.model_selection import train_test_split

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
    return partition(num_clients, int(cid), df)

def partition(num_clients: int, cid: int, df: pd.DataFrame):
    n = len(df)
    div = n // num_clients
    start = (cid - 1) * div
    end = (cid) * div
    part = df.iloc[start:, :] if cid == num_clients else df.iloc[start:end, :]
    y = part["label"]
    X = part.drop(["label"], axis=1)
    try:
        return train_test_split(X, y, test_size=0.3, random_state=None)
    except:
        print(f"The received cid is {cid}")
        part = df.iloc[:div, :]
        y = part["label"]
        X = part.drop(["label"], axis=1)
        return train_test_split(X, y, test_size=0.3, random_state=None)


def preprocess(df: pd.DataFrame):
    
    # Drop ID which is not helpful for training
    # Drop attack category because we only focus on detecting if it a traffic is an attack or not
    df = df.drop(['id', 'attack_cat'], axis=1)

    df_numeric = df.select_dtypes(include=[np.number])

    # Removing numeric outliers
    for feature in df_numeric.columns:
        if df_numeric[feature].max() > 10 and df_numeric[feature].max() > 10*df_numeric[feature].median():
            df[feature] = np.where(df[feature] < df[feature].quantile(0.95), df[feature], df[feature].quantile(0.95))

    # One hot encoding
    cols = ['proto', 'service', 'state']
    for each in cols:
        dummies = pd.get_dummies(df[each], prefix=each, drop_first=False)
        df = pd.concat([df, dummies], axis=1)
        df = df.drop(each, axis=1)

    # Normalise
    #Function to min-max normalize
    def normalize(df, cols):
        """
        @param df pandas DataFrame
        @param cols a list of columns to encode
        @return a DataFrame with normalized specified features
        """
        result = df.copy() # do not touch the original df
        for feature_name in cols:
            max_value = df[feature_name].astype('float').max()
            min_value = df[feature_name].astype('float').min()
            if max_value > min_value:
                result[feature_name] = (df[feature_name].astype('float') - min_value) / (max_value - min_value)
        return result

    return normalize(df, df.columns)