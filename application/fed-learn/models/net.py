from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import LSTM, Bidirectional, BatchNormalization, Conv1D, MaxPooling1D
import keras.backend as K

def sensitivity(y_true, y_pred): 
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    return true_positives / (possible_positives + K.epsilon())

def specificity(y_true, y_pred): 
    true_positives = K.sum(K.round(K.clip(1 - y_true * 1 - y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(1 - y_true, 0, 1)))
    return true_positives / (possible_positives + K.epsilon())

def get_model():
    model = Sequential()
    model.add(Conv1D(64, kernel_size=64, padding='same', activation='relu', input_shape=(196, 1)))
    model.add(MaxPooling1D(pool_size=(10)))
    model.add(BatchNormalization())
    model.add(Bidirectional(LSTM(64, return_sequences=False)))
    model.add(Dropout(0.6))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy', specificity, sensitivity])
    return model

def get_simple_model():
    model = Sequential()
    model.add(Conv1D(64, kernel_size=64, padding='same', activation='relu', input_shape=(196, 1)))
    model.add(Dropout(0.7))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam' , metrics=['accuracy', specificity, sensitivity])
    return model