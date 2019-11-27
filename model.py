import json
from os import listdir
from os.path import isdir, isfile, join

import cv2
import keras
<<<<<<< HEAD
from keras.layers 
import (Concatenate, Conv2D, Conv3D, Input, MaxPooling2D,
=======
import numpy as np
from keras.callbacks import Callback
from keras.layers import (Concatenate, Conv2D, Conv3D, Input, MaxPooling2D,
>>>>>>> origin/master
                          MaxPooling3D, Reshape)
from keras.models import Model
from keras.optimizers import SGD

from preprocessor import prepare_cakes


def prepare_X(imgs):
    if len(imgs) != 3:
        raise Exception
    cake_stack = np.stack([prepare_cakes(img)
                           for img in imgs], axis=2)
    cake = prepare_cakes(imgs[0])
    X_1 = np.empty((1, 256, 250, 3, 9))
    X_1[0, :, :, :, :] = cake_stack
    X_2 = np.empty((1, 256, 250, 9))
    X_2[0, :, :, :] = cake
    return [X_1, X_2]


class DataGenerator(keras.utils.Sequence):
    'Generates data for Keras'

    def __init__(self, list_IDs, batch_size=8, shuffle=True):
        'Initialization'
        self.batch_size = batch_size
        self.list_IDs = list_IDs
        self.shuffle = shuffle
        self.on_epoch_end()

    def __len__(self):
        'Denotes the number of batches per epoch'
        return int(np.floor(len(self.list_IDs) / self.batch_size))

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        # Find list of IDs
        list_IDs_temp = [self.list_IDs[k] for k in indexes]

        # Generate data
        X, y = self.__data_generation(list_IDs_temp)

        return X, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(len(self.list_IDs))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)

    def __data_generation(self, list_IDs_temp):
        # X : (n_samples, *dim, n_channels)
        'Generates data containing batch_size samples'
        # Initialization
        X_1 = np.empty((self.batch_size, 256, 250, 3, 9))
        X_2 = np.empty((self.batch_size, 256, 250, 9))
        y = np.empty((self.batch_size, 128, 125))

        for i, ID in enumerate(list_IDs_temp):
            with open('./train/' + ID, 'r') as f:
                json_file = json.load(f)
                X_1[i, :, :, :, :] = np.array(json_file['x'][0])
                X_2[i, :, :, :] = np.array(json_file['x'][1])

                y[i] = np.array(json_file['y'])

        return [X_1, X_2], y


class ModelSaver(Callback):
    def on_epoch_end(self, epoch, logs={}):
        # or save after some epoch, each k-th epoch etc.
        if epoch == 1 or epoch % 5 == 0:
            self.model.save(f"./models/model_{epoch:05}.hd5")


class CystCNN():
    def __init__(self, weights_file=None):
        self._prepare_model()
        if weights_file is not None:
            self.model.load_weights(weights_file)

    def _prepare_model(self):
        input_1 = Input(shape=(256, 250, 3, 9))
        input_2 = Input(shape=(256, 250, 9))

        output_1 = Conv3D(9, (1, 1, 3))(input_1)
        output_2 = Reshape((256, 250, 9))(output_1)

        output_3 = MaxPooling3D(pool_size=(2, 2, 1))(input_1)
        output_4 = Conv3D(9, (25, 25, 3), padding='same')(output_3)
        output_5 = Conv3D(9, (1, 1, 3))(output_4)
        output_6 = Reshape((128, 125, 9))(output_5)

        input_2_output_2 = Concatenate()([input_2, output_2])
        output_7 = Conv2D(8, (10, 10), padding='same')(input_2_output_2)
        output_8 = MaxPooling2D(pool_size=(2, 2))(output_7)
        output_8_output_6 = Concatenate()([output_8, output_6])
        output_9 = Conv2D(8, (25, 25), padding='same')(output_8_output_6)
        prob_map = Conv2D(1, (1, 1), padding='same')(output_9)
        output = output_2 = Reshape((128, 125))(prob_map)

        optimizer = SGD(learning_rate=0.001, momentum=0.75, nesterov=True)
        self.model = Model(inputs=[input_1, input_2], output=output)
        self.model.compile(optimizer, loss='binary_crossentropy')
        self.model.summary()

    def train(self, epochs, batch_size, train_dir='./train'):
        fileNames = [f for f in listdir(
            train_dir) if isfile(join(train_dir, f))]
        training_data = fileNames[:len(fileNames)-20]
        validation_data = fileNames[len(fileNames)-20:]

        training_generator = DataGenerator(training_data, batch_size=8)
        validation_generator = DataGenerator(validation_data, batch_size=8)
        saver = ModelSaver()
        self.model.fit_generator(generator=training_generator,
                                 validation_data=validation_generator,
                                 callbacks=[saver],
                                 epochs=epochs,
                                 verbose=batch_size)
        self.model.save(f"./my_model.hd5")

    def predict(self, X):
        return self.model.predict(X)


# To train...
# model.fit([input1, input2], Y,
#           validation_data=([v_input_1, v_input_2], v_Y),
#           batch_size=batch_size, epoch=epoch)
if __name__ == "__main__":
    model = CystCNN()
    model.train(1500, 8)
