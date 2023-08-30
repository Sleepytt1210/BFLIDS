from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import Bidirectional, LSTM
from keras.metrics import SpecificityAtSensitivity, SensitivityAtSpecificity

def get_model():
    model = Sequential()
    model.add(Bidirectional(LSTM(30, return_sequences=True), input_shape=(1, 196)))
    model.add(Bidirectional(LSTM(30, return_sequences=False)))
    model.add(Dropout(0.3))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy', SensitivityAtSpecificity(0.5, name="Sensitivity"), SpecificityAtSensitivity(0.5, name="Specificity")])
    return model